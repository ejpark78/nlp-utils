#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
import re
from argparse import Namespace
from copy import deepcopy
from datetime import datetime, timedelta
from time import sleep
from urllib.parse import parse_qs, urljoin

import requests
import urllib3
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.web_news.base import WebNewsBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class WebNewsCrawler(WebNewsBase):
    """웹 뉴스 크롤러"""

    def __init__(self):
        super().__init__()

        self.env = None

        self.trace_depth = 0
        self.trace_list_count = -1

        self.date_step = 1

        self.update_date = False

        self.job_sub_category = None

    def set_env(self, env: Namespace) -> None:
        self.env = env

        self.trace_depth = 0
        self.trace_list_count = -1

        self.job_sub_category = env.sub_category.split(',') if env.sub_category != '' else []

        self.date_step = env.date_step

        if env.date_range is None:
            self.update_date = True
            self.update_date_range()
        else:
            token = env.date_range.split('~', maxsplit=1)

            dt_start = parse_date(token[0])
            dt_end = dt_start + relativedelta(months=1)

            if len(token) > 1:
                dt_end = parse_date(token[1])

            self.date_range = {
                'end': self.timezone.localize(dt_end),
                'start': self.timezone.localize(dt_start),
            }

            today = datetime.now(self.timezone)
            if self.date_range['end'] > today:
                self.date_range['end'] = today

        self.page_range = {
            'start': 1,
            'end': 900,
            'step': env.page_step
        }

        if env.page_range is not None:
            pg_start, pg_end = env.page_range.split('~', maxsplit=1)

            self.page_range = {
                'start': int(pg_start),
                'end': int(pg_end),
                'step': env.page_step
            }

        return

    def batch(self) -> None:
        """카테고리 하위 목록을 크롤링한다."""
        self.set_env(env=self.init_arguments())

        self.config = self.open_config(filename=self.env.config)

        # 카테고리 하위 목록을 크롤링한다.
        for job in self.config['jobs']:
            # override elasticsearch config
            job['host'] = self.cache_info['host'] = os.getenv('ELASTIC_SEARCH_HOST', job['host'])
            job['index'] = os.getenv('ELASTIC_SEARCH_INDEX', job['index'])
            job['http_auth'] = self.cache_info['http_auth'] = os.getenv('ELASTIC_SEARCH_AUTH', job['http_auth'])

            self.trace_url_list(job=job)

        return

    def trace_url_list(self, job: dict) -> None:
        """url_frame 목록을 반복한다."""
        # url 목록 반복
        for url in job['list']:
            if url['url_frame'][0] == '#':
                continue

            if len(self.job_sub_category) > 0 and 'category' in url and url['category'] not in self.job_sub_category:
                continue

            if url['url_frame'].find('date') < 0:
                # page 단위로 크롤링한다.
                self.trace_page_list(url=url, job=job, dt=None)
                continue

            # 날짜 지정시
            date_list = list(rrule(DAILY, dtstart=self.date_range['start'], until=self.date_range['end']))

            if self.date_step < 0:
                date_list = sorted(date_list, reverse=True)

            for dt in date_list:
                date_now = datetime.now(self.timezone)
                if dt > date_now + timedelta(1):
                    break

                # page 단위로 크롤링한다.
                self.trace_page_list(url=url, job=job, dt=dt)

        return

    def trace_page_list(self, url: dict, job: dict, dt: datetime = None) -> None:
        """뉴스 목록을 크롤링한다."""
        self.trace_depth = 0
        self.trace_list_count = -1

        # start 부터 end 까지 반복한다.
        for page in range(self.page_range['start'], self.page_range['end'] + 1, self.page_range['step']):
            # 쿼리 url 생성
            q = dict(page=page)
            if dt is not None:
                q['date'] = dt.strftime(url['date_format'])

            if url['url_frame'].find('{page}') > 0:
                url['url'] = url['url_frame'].format(**q)

            if 'category' in url:
                job['category'] = url['category']

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '뉴스 목록 크롤링',
                'url': url['url'],
                'query': q,
                'date': dt.strftime('%Y-%m-%d') if dt is not None else '',
            })

            # 기사 목록 조회
            resp = self.get_html_page(url_info=url, tags='#list')
            if resp is None:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '뉴스 목록 조회 에러',
                    'url': url['url'],
                    'query': q,
                    'date': dt.strftime('%Y-%m-%d') if dt is not None else '',
                })
                continue

            # category 만 업데이트할 경우
            early_stop = self.update_category(html=resp, url_info=url, job=job, date=dt)
            if self.env.update_category_only is True:
                if early_stop is True:
                    break

                sleep(self.env.sleep)
                continue

            # 문서 저장
            early_stop, trace_list = self.trace_news(html=resp, url_info=url, job=job, date=dt)
            if trace_list is None:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': 'trace_list 가 없음: 마지막 페이지',
                    'url': url['url'],
                    'category': job['category'],
                    'date': dt.strftime('%Y-%m-%d') if dt is not None else '',
                })
                break

            if early_stop is True:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '기사 목록 끝에 도달: 종료',
                    'url': url['url'],
                    'category': job['category'],
                    'date': dt.strftime('%Y-%m-%d') if dt is not None else '',
                })
                break

            sleep(self.env.sleep)

        return

    def update_category(self, html: str, url_info: dict, job: dict, date: datetime) -> bool:
        """카테고리 정보를 갱신한다."""
        if date is None and job['index'].find('{year}') > 0:
            return False

        # 기사 목록을 추출한다.
        trace_list = self.get_trace_list(html=html, url_info=url_info)
        if trace_list is None:
            return True

        # 디비에 연결한다.
        elastic_utils = self.open_elasticsearch(date=date, job=job)

        # 개별 뉴스를 따라간다.
        doc_ids = set()
        bulk_data = {}

        for trace in trace_list:
            item = self.parse_tag(
                resp=trace,
                url_info=url_info,
                base_url=url_info['url'],
                parsing_info=self.config['parsing']['list'],
            )
            if item is None or 'url' not in item:
                continue

            item['url'] = urljoin(url_info['url'], item['url'])
            item['category'] = job['category']

            doc_id = self.get_doc_id(url=item['url'], job=job, item=item)
            item['_id'] = doc_id

            doc_ids.add(doc_id)
            bulk_data[doc_id] = item

        doc_list = []
        elastic_utils.index = elastic_utils.get_target_index(
            tag=elastic_utils.get_index_year_tag(date=date),
            index=job['index'],
            split_index=job['split_index'],
        )

        elastic_utils.get_by_ids(
            id_list=list(doc_ids),
            index=elastic_utils.index,
            source=['category', 'document_id'],
            result=doc_list
        )

        for doc in doc_list:
            if 'category' not in doc or doc['category'].strip() == '':
                continue

            if 'document_id' not in doc:
                continue

            doc_id = doc['document_id']

            category = doc['category'].split(',')
            category += bulk_data[doc_id]['category'].split(',')

            bulk_data[doc_id]['category'] = ','.join(list(set(category)))

        for doc in bulk_data.values():
            elastic_utils.save_document(document=doc, delete=False)

        elastic_utils.flush()

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '카테고리 업데이트',
            'length': len(trace_list),
            'category': job['category'],
        })

        return False

    @staticmethod
    def open_elasticsearch(date: datetime, job: dict) -> ElasticSearchUtils:
        """디비에 연결한다."""
        index_tag = None
        if date is not None:
            index_tag = date.year

        if 'split_index' not in job:
            job['split_index'] = False

        return ElasticSearchUtils(
            tag=index_tag,
            host=job['host'],
            index=None,
            bulk_size=20,
            http_auth=job['http_auth'],
            split_index=job['split_index'],
        )

    def trace_news(self, html: str, url_info: dict, job: dict, date: datetime) -> (bool, list):
        """개별 뉴스를 따라간다."""
        # 기사 목록을 추출한다.
        trace_list = self.get_trace_list(html=html, url_info=url_info)
        if trace_list is None:
            return True, trace_list

        # url 저장 이력 조회
        doc_history = self.get_history(name='doc_history', default=set())

        # 베이스 url 추출
        base_url = self.parser.parse_url(url_info['url'])[1]

        # 디비에 연결한다.
        elastic_utils = self.open_elasticsearch(date=date, job=job)

        # 개별 뉴스를 따라간다.
        for trace in trace_list:
            item = self.parse_tag(
                resp=trace,
                url_info=url_info,
                base_url=base_url,
                parsing_info=self.config['parsing']['list'],
            )
            if item is None or 'url' not in item:
                continue

            item['url'] = urljoin(base_url, item['url'])

            # 카테고리 업데이트
            item['category'] = job['category']

            # 기존 크롤링된 문서를 확인한다.
            doc_id = self.get_doc_id(url=item['url'], job=job, item=item)
            if doc_id is None:
                continue

            if date is None and 'date' in item:
                date = item['date']

            is_skip = False
            if self.env.overwrite is False:
                elastic_utils.index = elastic_utils.get_target_index(
                    tag=elastic_utils.get_index_year_tag(date=date),
                    index=job['index'],
                    split_index=job['split_index'],
                )

                is_skip = self.check_doc_id(
                    url=item['url'],
                    index=elastic_utils.index,
                    doc_id=doc_id,
                    doc_history=doc_history,
                    elastic_utils=elastic_utils,
                )

                if 'check_id' not in url_info or url_info['check_id'] is False:
                    is_skip = False

            if is_skip is True:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '크롤링된 뉴스가 있음',
                    'doc_id': doc_id,
                    'url': item['url'],
                    'doc_url': elastic_utils.get_doc_url(document_id=doc_id)
                })
                continue

            # 기사 본문 조회
            article, article_html = self.get_article(
                job=job,
                item=item,
                doc_id=doc_id,
                offline=False,
            )

            # 기사 저장
            if article is None:
                # 에러난 url 기록
                item['_id'] = doc_id
                item['raw_html'] = article_html

                elastic_utils.save_document(
                    document=item,
                    index=job['index'].replace('-{year}') + '-error'
                )
                elastic_utils.flush()
            else:
                self.save_article(
                    job=job,
                    doc=item,
                    html=article_html,
                    article=article,
                    elastic_utils=elastic_utils,
                )

            doc_history.add(doc_id)

            # 후처리 작업 실행
            if 'post_process' not in job:
                job['post_process'] = None

            if self.env.skip_post_process is True:
                job['post_process'] = None

            self.post_process_utils.insert_job(
                job=job,
                document=article,
                post_process_list=job['post_process'],
            )

            self.logger.info(msg={
                'level': 'INFO',
                'message': '뉴스 본문 크롤링: 슬립',
                'sleep_time': self.env.sleep,
            })
            sleep(self.env.sleep)

        # 목록 길이 저장
        if self.trace_list_count < 0:
            self.trace_list_count = len(trace_list)
        elif self.trace_list_count > len(trace_list) + 3:
            return True, trace_list

        # 캐쉬 저장
        self.set_history(value=doc_history, name='doc_history')

        # 다음 페이지 정보가 있는 경우
        self.trace_next_page(html=html, url_info=url_info, job=job, date=date)

        return False, trace_list

    def get_article(self, doc_id: str, item: dict, job: dict, offline: bool = False) -> (dict, str):
        """기사 본문을 조회한다."""
        article_url = None
        if 'article' in job:
            article_url = job['article']
            article_url['url'] = item['url']

        if offline is True:
            if 'raw_html' in item:
                resp = item['raw_html']
            elif 'html_content' not in item:
                return None, ''
            else:
                resp = item['html_content']

            # 추출된 html_contents 가 없는 경우: 다시 크롤링
            if isinstance(resp, list):
                resp = self.get_html_page(url_info=article_url, tags='#article')
        else:
            resp = self.get_html_page(url_info=article_url, tags='#article')
            if resp is None:
                return None, ''

        # 문서 저장
        article = self.parse_tag(
            resp=resp,
            base_url=item['url'],
            url_info=article_url,
            parsing_info=self.config['parsing']['article'],
        )

        if article is None:
            return None, str(resp)

        if len(article) == 0:
            # 삭제된 기사
            return None, str(resp)

        article['_id'] = doc_id

        # 댓글 post process 처리
        if 'post_request' in job:
            req_params = deepcopy(item)
            req_params.update(article)

            for request_info in job['post_request']:
                self.post_request(
                    article=article,
                    url_info=request_info,
                    req_params=req_params,
                )

        return article, str(resp)

    def post_request(self, req_params: dict, url_info: dict, article: dict) -> dict:
        """댓글을 요청한다."""
        if url_info['response_type'] != 'json':
            return article

        headers = self.headers['desktop']
        if 'headers' in url_info:
            headers.update(url_info['headers'])

        url = url_info['url_frame'].format(**req_params)

        try:
            if url_info['method'] != "POST":
                resp = requests.get(
                    url=url,
                    verify=False,
                    timeout=60,
                    headers=headers,
                    allow_redirects=True,
                )
            else:
                body = url_info['data'].format(**req_params)
                body = parse_qs(body)

                resp = requests.post(
                    url=url,
                    data=body,
                    verify=False,
                    timeout=60,
                    headers=headers,
                    allow_redirects=True,
                )
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'post request 조회 에러',
                'url': url,
                'exception': str(e),
            })
            return article

        # 결과 파싱
        try:
            req_result = resp.json()
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'post request 파싱 에러',
                'url': url,
                'exception': str(e),
            })
            return article

        self.save_raw_html(
            url_info=url_info,
            status_code=0,
            error='',
            content=json.dumps(req_result, ensure_ascii=False),
            content_type='json',
            tags='#reply'
        )

        result = []
        self.get_dict_value(
            data=req_result,
            result=result,
            key_list=url_info['field'].split('.'),
        )

        if len(result) > 0:
            article[url_info['key']] = result

        return article

    def set_timezone_at_reply_date(self, doc: dict) -> dict:
        """댓글 날짜에 timezone 정보를 설정한다."""
        for k in ['reply_list']:
            if k not in doc or isinstance(doc[k], list) is False:
                continue

            for item in doc[k]:
                if 'date' not in item:
                    continue

                if isinstance(item['date'], str):
                    item['date'] = parse_date(item['date']).astimezone(self.timezone)

        return doc

    def trace_next_page(self, html, url_info, job, date) -> None:
        """다음 페이지를 따라간다."""
        if 'trace_next_page' not in self.config['parsing']:
            return

        # html 이 json 인 경우
        if isinstance(html, dict) or isinstance(html, list):
            return

        # 한번에 따라갈 깊이
        trace_tag = self.config['parsing']['trace_next_page']
        if trace_tag['max_trace'] > 0:
            if trace_tag['max_trace'] < self.trace_depth:
                self.trace_depth = 0
                return

        self.trace_depth += 1

        # 다음 페이지 url 추출
        trace_list = []
        soup = self.parser.parse_html(
            html=html,
            parser_type=self.config['parsing']['parser'],
        )
        self.parser.trace_tag(
            soup=soup,
            index=0,
            result=trace_list,
            tag_list=trace_tag['tag'],
        )

        for tag in trace_list:
            if tag.has_attr('href') is False:
                continue

            url = urljoin(url_info['url'], tag['href'])
            if 'replace' in trace_tag:
                for pattern in trace_tag['replace']:
                    url = re.sub(pattern['from'], pattern['to'], url, flags=re.DOTALL)

            next_url = self.config['parsing']
            next_url['url'] = url

            resp = self.get_html_page(url_info=self.config['parsing'], tags='#article #next_page')
            if resp is None:
                continue

            self.logger.info(msg={
                'level': 'INFO',
                'message': '다음페이지 크롤링: 슬립',
                'sleep_time': self.env.sleep,
            })

            sleep(self.env.sleep)

            self.trace_news(html=resp, url_info=url_info, job=job, date=date)

        return

    def remove_date_column(self, doc: dict, html: str) -> None:
        """날짜 필드를 확인해서 날짜 파싱 오류일 경우, 날짜 필드를 삭제한다."""
        if 'date' not in doc:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'date 필드가 없습니다.',
            })
            return

        str_e = ''
        parsing_error = False
        if doc['date'] == '':
            str_e = 'date missing'
            parsing_error = True

        if parsing_error is False and isinstance(doc['date'], str):
            try:
                doc['date'] = parse_date(doc['date'])
                doc['date'] = doc['date'].astimezone(tz=self.timezone)
            except Exception as e:
                parsing_error = True
                str_e = str(e)

        if parsing_error is True:
            doc['parsing_error'] = True
            doc['raw_html'] = str(html)

            self.logger.error(msg={
                'level': 'ERROR',
                'message': '날짜 파싱 에러: date 필드 삭제',
                'exception': str_e,
                'date': doc['date'],
            })

            if 'date' in doc:
                del doc['date']

        return

    def save_article(self, html: str, doc: dict, article: dict, elastic_utils: ElasticSearchUtils, job: dict) -> dict:
        """크롤링한 문서를 저장한다."""
        # 후처리
        doc = self.parser.merge_values(item=doc)
        article = self.parser.merge_values(item=article)

        error = False

        # 파싱 에러 처리
        if 'html_content' in article and len(article['html_content']) != 0:
            doc.update(article)
        elif 'html' in article and len(article['html']) != 0:
            doc.update(article)
        else:
            doc['parsing_error'] = True
            doc['raw_html'] = str(html)

            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'html_content 필드가 없음',
                'url': doc['url'],
            })

        if 'parsing_error' not in doc:
            if 'title' not in doc or len(doc['title']) == 0:
                doc['parsing_error'] = True
                doc['raw_html'] = str(html)

                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'title 필드가 없음',
                    'url': doc['url'],
                })

        # 날짜 필드 오류 처리
        self.remove_date_column(doc=doc, html=html)

        # 문서 아이디 추출
        doc['curl_date'] = datetime.now(self.timezone).isoformat()

        # 에러인 경우
        if error is True:
            doc['raw_html'] = str(html)

            elastic_utils.save_document(
                document=doc,
                index=job['index'].replace('-{year}', '') + '-error'
            )
            elastic_utils.flush()
            return doc

        # 인덱스 변경
        if 'date' in doc:
            elastic_utils.index = elastic_utils.get_target_index(
                tag=elastic_utils.get_index_year_tag(date=doc['date']),
                index=job['index'],
                split_index=job['split_index'],
            )

        # category 필드 병합
        doc = self.merge_category(doc=doc, elastic_utils=elastic_utils)

        # 문서 저장
        elastic_utils.save_document(document=doc)
        flag = elastic_utils.flush()

        # 성공 로그 표시
        if flag is True:
            doc_info = {}
            for k in ['document_id', 'date', 'title']:
                if k in doc:
                    doc_info[k] = doc[k]

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '기사 저장 성공',
                'doc_url': elastic_utils.get_doc_url(document_id=doc['document_id']),
                **doc_info,
            })

        return doc

    @staticmethod
    def merge_category(doc: dict, elastic_utils: ElasticSearchUtils) -> dict:
        """category 정보를 병합한다."""
        doc_id = None

        if '_id' in doc:
            doc_id = doc['_id']

        if 'document_id' in doc:
            doc_id = doc['document_id']

        if doc_id is None:
            return doc

        resp = elastic_utils.conn.mget(
            body={
                'docs': [{'_id': doc_id}]
            },
            index=elastic_utils.index,
            _source=['category'],
        )

        for n in resp['docs']:
            if '_source' not in n:
                continue

            category = n['_source']['category'].split(',')
            category += doc['category'].split(',')

            doc['category'] = ','.join(list(set(category)))

        return doc

    def get_doc_id(self, url: str, job: dict, item: dict) -> str or None:
        """문서 아이디를 반환한다."""
        id_frame = job['article']['document_id']

        q, _, url_info = self.parser.parse_url(url)

        result = '{}.{}'.format(url_info.path, '.'.join(q.values()))

        if id_frame['type'] == 'path':
            result = url_info.path

            for pattern in id_frame['replace']:
                result = re.sub(pattern['from'], pattern['to'], result, flags=re.DOTALL)
        elif id_frame['type'] == 'query':
            if self.env.overwrite is False and len(q) == 0:
                self.logger.info(msg={
                    'level': 'INFO',
                    'message': '중복 문서, 건너뜀',
                    'url': url,
                })

                return None

            try:
                result = id_frame['frame'].format(**q)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'url fame 에러',
                    'q': q,
                    'id_frame': id_frame['frame'],
                    'exception': str(e),
                })
        elif id_frame['type'] == 'value':
            result = id_frame['frame'].format(**item)

        return result.strip()

    def get_trace_list(self, html: str, url_info: dict) -> list or None:
        """trace tag 목록을 추출해서 반환한다."""
        trace_list = []
        if 'parser' in url_info and url_info['parser'] == 'json':
            column = url_info['trace']
            if column in html:
                trace_list = html[column]

            str_trace_list = json.dumps(trace_list, ensure_ascii=False, sort_keys=True)
        else:
            soup = self.parser.parse_html(
                html=html,
                parser_type=self.config['parsing']['parser'],
            )

            self.parser.trace_tag(
                soup=soup,
                index=0,
                result=trace_list,
                tag_list=self.config['parsing']['trace'],
            )

            str_trace_list = ''
            for item in trace_list:
                str_trace_list += str(item)

        if len(trace_list) == 0:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'trace_list 가 없음',
                'trace_size': len(trace_list),
                'sleep_time': self.env.sleep,
            })

            sleep(self.env.sleep)
            return None

        if self.env.update_category_only is True:
            return trace_list

        self.set_history(
            name='trace_list',
            value=set(str_trace_list),
        )

        return trace_list

    def parse_tag(self, resp, url_info: dict, parsing_info: list, base_url: str):
        """trace tag 하나를 파싱해서 반환한다."""
        # json 인 경우 맵핑값 매칭
        if 'parser' in url_info and url_info['parser'] == 'json':
            item = self.parser.parse_json(resp=resp, url_info=url_info)
        else:
            if isinstance(resp, str) or isinstance(resp, bytes):
                resp = self.parser.parse_html(
                    html=resp,
                    parser_type=self.config['parsing']['parser'],
                )

            # 목록에서 기사 본문 링크 추출
            item = self.parser.parse(
                html=None,
                soup=resp,
                base_url=base_url,
                parsing_info=parsing_info,
            )

        # url 추출
        if 'url' in item and isinstance(item['url'], list):
            if len(item['url']) > 0:
                item['url'] = item['url'][0]
            else:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'trace tag에서 url 추출 에러',
                    'resp': str(resp)[:200],
                })
                return None

        if len(item) == 0:
            text = ''
            if isinstance(resp, BeautifulSoup):
                text = resp.get_text()
            elif isinstance(resp, str):
                text = BeautifulSoup(resp, 'html5lib').get_text()

            # 삭제된 페이지
            empty = [
                '페이지를 찾을 수 없습니다',
                '언론사 요청에 의해 삭제된 기사입니다.',
                '노출 중단 된 기사입니다.',
                'Service Unavailable',
                'Service Temporarily Unavailable'
            ]
            for m in empty:
                if text.find(m) > 0:
                    return {}

            # 에러 메세지 출력
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'HTML 파싱 에러',
                'resp': str(resp)[:200],
                'text': text,
                'url': url_info['url'],
            })

            return None

        return item

    @staticmethod
    def init_arguments() -> Namespace:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--overwrite', action='store_true', default=False, help='덮어쓰기')

        # 작업 아이디
        parser.add_argument('--category', default='', help='작업 카테고리')
        parser.add_argument('--job-id', default='', help='작업 아이디')
        parser.add_argument('--sub-category', default='', help='하위 카테고리')

        parser.add_argument('--date-range', default=None, help='date 날짜 범위: 2000-01-01~2019-04-10')
        parser.add_argument('--date-step', default=-1, type=int, help='date step')

        parser.add_argument('--page-range', default=None, help='page 범위: 1~100')
        parser.add_argument('--page-step', default=1, type=int, help='page step')

        parser.add_argument('--sleep', default=10, type=float, help='sleep time')

        # 설정파일
        parser.add_argument('--config', default=None, type=str, help='설정 파일 정보')

        parser.add_argument('--update-category-only', action='store_true', default=False, help='category 정보만 업데이트')

        parser.add_argument('--skip-post-process', action='store_true', default=False, help='후처리 사용 여부')
        parser.add_argument('--skip-check-history', action='store_true', default=False, help='히스토리 점검 여부')

        return parser.parse_args()


if __name__ == '__main__':
    WebNewsCrawler().batch()
