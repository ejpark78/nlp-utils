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
from dateutil.rrule import rrule, DAILY
from dotty_dict import dotty

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.web_news.base import WebNewsBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class WebNewsCrawler(WebNewsBase):
    """웹 뉴스 크롤러"""

    def __init__(self):
        super().__init__()

        self.params = None

        self.trace_depth = 0
        self.trace_list_count = -1

        self.update_date = False

        self.job_sub_category = None

    @staticmethod
    def open_elasticsearch(date: datetime, job: dict) -> ElasticSearchUtils:
        """디비에 연결한다."""
        index_tag = None
        if date is not None:
            index_tag = date.year

        return ElasticSearchUtils(
            tag=index_tag,
            host=job['host'],
            index=None,
            bulk_size=20,
            http_auth=job['http_auth'],
        )

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

    def get_article_page(self, item: dict, offline: bool = False) -> str:
        """기사 본문을 조회한다."""
        resp = None
        if offline is True:
            if 'html' in item:
                resp = item['html']
            elif 'html_content' in item:
                resp = item['html_content']
            else:
                return ''

        if resp is None:
            resp = self.get_html_page(url_info=item)

        if resp is None:
            return ''

        return resp

    def post_request(self, job: dict, article: dict, item: dict) -> None:
        """댓글을 요청한다."""
        if 'post_request' not in job:
            return

        req_params = {
            **deepcopy(item),
            **deepcopy(article)
        }

        for url_info in job['post_request']:
            if url_info['response_type'] != 'json':
                return

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
                return

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
                return

            result = []
            self.get_dict_value(
                data=req_result,
                result=result,
                key_list=url_info['field'].split('.'),
            )

            if len(result) > 0:
                article[url_info['key']] = result

        return

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

    def trace_next_page(self, html: str, url_info: dict, job: dict, date: datetime) -> None:
        """다음 페이지를 따라간다."""
        if 'trace_next_page' not in self.config['parsing']:
            return

        # html 이 json 인 경우
        if isinstance(html, dict) or isinstance(html, list):
            return

        trace_tag = self.config['parsing']['trace_next_page']

        if len(trace_tag) == 0:
            return

        # 한번에 따라갈 깊이
        if trace_tag['max_trace'] > 0:
            if trace_tag['max_trace'] < self.trace_depth:
                self.trace_depth = 0
                return

        self.trace_depth += 1

        # 다음 페이지 url 추출
        soup = self.parser.parse_html(
            html=html,
            parser_type=self.config['parsing']['parser'],
        )

        trace_list = []
        self.parser.trace_tag(
            soup=soup,
            index=0,
            result=trace_list,
            tag_list=trace_tag['value'],
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

            resp = self.get_html_page(url_info=self.config['parsing'])
            if resp is None:
                continue

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '다음페이지 크롤링: 슬립',
                'sleep_time': self.params.sleep,
            })

            sleep(self.params.sleep)

            self.trace_news(html=resp, url_info=url_info, job=job, date=date)

        return

    def remove_date_column(self, doc: dict) -> None:
        """날짜 필드를 확인해서 날짜 파싱 오류일 경우, 날짜 필드를 삭제한다."""
        if 'date' not in doc:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'date 필드가 없습니다.',
            })
            return

        if isinstance(doc['date'], str) and doc['date'] == '':
            del doc['date']
            return

        if isinstance(doc['date'], str):
            try:
                doc['date'] = parse_date(doc['date'])
                doc['date'] = doc['date'].astimezone(tz=self.timezone)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '날짜 파싱 에러: date 필드 삭제',
                    'exception': str(e),
                    'date': doc['date'],
                })

                del doc['date']
                return

        return

    def save_article(self, html: str, doc: dict, article: dict, elastic_utils: ElasticSearchUtils, job: dict) -> dict:
        """크롤링한 문서를 저장한다."""
        # 후처리
        doc = self.parser.merge_values(item=doc)
        article = self.parser.merge_values(item=article)

        error = False

        # 파싱 에러 처리
        if 'html' in article and len(article['html']) != 0:
            doc.update(article)
        elif 'html_content' in article and len(article['html_content']) != 0:
            doc.update(article)
        else:
            doc['status'] = 'parsing_error'
            if 'html' not in doc or doc['html'] == '':
                doc['html'] = str(html)

            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'html_content 필드가 없음',
                'url': doc['url'],
            })

        # 날짜 필드 오류 처리
        self.remove_date_column(doc=doc)

        # 문서 아이디 추출
        doc['@timestamp'] = datetime.now(self.timezone).isoformat()

        # 에러인 경우
        if error is True:
            if 'html' not in doc or doc['html'] == '':
                doc['html'] = str(html)

            elastic_utils.save_document(
                document=doc,
                index=job['index'].replace('-{year}', ''),
                delete=False,
            )
            elastic_utils.flush()
            return doc

        # 인덱스 변경
        if 'date' in doc:
            elastic_utils.index = elastic_utils.get_target_index(
                tag=elastic_utils.get_index_year_tag(date=doc['date']),
                index=job['index'],
            )

        # category 필드 병합
        doc = self.merge_category(doc=doc, elastic_utils=elastic_utils)

        # 문서 저장
        elastic_utils.save_document(document=doc, delete=False)
        flag = elastic_utils.flush()

        # 성공 로그 표시
        if flag is True:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '기사 저장 성공',
                'url': doc['url'],
                'doc_url': elastic_utils.get_doc_url(document_id=doc['document_id']),
                **{x: doc[x] for x in ['document_id', 'date', 'title'] if x in doc},
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
            if self.params.overwrite is False and len(q) == 0:
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

    @staticmethod
    def flatten(trace_list) -> list:
        result = []

        for item in trace_list:
            if isinstance(item, dict):
                result.append(item)
                continue

            new_item = {}
            for x in item:
                if x is None:
                    continue

                new_item = {
                    **new_item,
                    **x
                }

            result.append(new_item)

        return result

    def get_trace_list(self, html: str or dict, url_info: dict) -> list or None:
        """trace tag 목록을 추출해서 반환한다."""
        trace_list = []
        if 'parser' in url_info and url_info['parser'] == 'json':
            column = url_info['trace']

            dot = dotty(html)
            trace_list = list(dot[column]) if column in dot else []
            trace_list = self.flatten(trace_list=trace_list)

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
                'sleep_time': self.params.sleep,
            })

            sleep(self.params.sleep)
            return None

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
                parser_version=self.config['parsing']['version'] if 'version' in self.config['parsing'] else None,
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

    def is_skip(self, es: ElasticSearchUtils, date: datetime, job: dict, url: str, doc_id: str,
                doc_history: set) -> bool:
        if self.params.overwrite is True:
            return False

        es.index = es.get_target_index(
            tag=es.get_index_year_tag(date=date),
            index=job['index'],
        )

        is_skip = self.check_doc_id(
            url=url,
            index=es.index,
            doc_id=doc_id,
            doc_history=doc_history,
            es=es,
        )
        if is_skip is True:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '크롤링된 뉴스가 있음',
                'doc_id': doc_id,
                'url': url,
                'doc_url': es.get_doc_url(document_id=doc_id)
            })

            return True

        return False

    def trace_news(self, html: str, url_info: dict, job: dict, date: datetime) -> (bool, list):
        """개별 뉴스를 따라간다."""
        # 기사 목록을 추출한다.
        trace_list = self.get_trace_list(html=html, url_info=url_info)
        if trace_list is None:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'trace_list 가 없음',
                'url': url_info['url'] if 'url' in url_info else '',
                **job,
            })
            return True, trace_list

        # url 저장 이력 조회
        doc_history = self.get_history(name='doc_history', default=set())

        # 디비에 연결한다.
        elastic_utils = self.open_elasticsearch(date=date, job=job)

        # 베이스 url 추출
        base_url = self.parser.parse_url(url_info['url'])[1]

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
            item['category'] = job['category']

            if date is None and 'date' in item:
                date = item['date']

            # 기존 크롤링된 문서를 확인한다.
            doc_id = self.get_doc_id(url=item['url'], job=job, item=item)
            if doc_id is None:
                continue

            if self.is_skip(es=elastic_utils, date=date, job=job, url=item['url'], doc_id=doc_id,
                            doc_history=doc_history) is True:
                continue

            # 기사 본문 조회
            article_html = self.get_article_page(item=item, offline=False)

            # 문서 저장
            article = self.parse_tag(
                resp=article_html,
                url_info=item,
                base_url=item['url'],
                parsing_info=self.config['parsing']['article'],
            )
            if article is None or len(article) == 0:
                continue

            article['_id'] = doc_id

            # 댓글 post process 처리
            self.post_request(article=article, job=job, item=item)

            # 기사 저장
            self.save_article(
                job=job,
                doc=item,
                html=article_html,
                article=article,
                elastic_utils=elastic_utils,
            )

            doc_history.add(doc_id)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '뉴스 본문 크롤링: 슬립',
                'sleep_time': self.params.sleep,
            })
            sleep(self.params.sleep)

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

    def trace_page(self, url_info: dict, job: dict, dt: datetime = None) -> None:
        """뉴스 목록을 크롤링한다."""
        self.trace_depth = 0
        self.trace_list_count = -1

        # start 부터 end 까지 반복한다.
        for page in range(self.page_range['start'], self.page_range['end'] + 1, self.page_range['step']):
            # 쿼리 url 생성
            q = dict(page=page)
            if dt is not None:
                q['date'] = dt.strftime(url_info['date_format'])

            url_info['url'] = url_info['url_frame'].format(**q)

            if 'category' in url_info:
                job['category'] = url_info['category']

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '뉴스 목록 크롤링',
                'url': url_info['url'] if 'url' in url_info else '',
                'query': q,
                'date': dt.strftime('%Y-%m-%d') if dt is not None else '',
            })

            # 기사 목록 조회
            resp = self.get_html_page(url_info=url_info, log_msg={'trace': '뉴스 목록 조회'})
            if resp is None:
                continue

            # category 만 업데이트할 경우
            early_stop = self.update_category(html=resp, url_info=url_info, job=job, date=dt)
            if self.params.update_category_only is True:
                if early_stop is True:
                    break

                sleep(self.params.sleep)
                continue

            # 문서 저장
            early_stop, trace_list = self.trace_news(html=resp, url_info=url_info, job=job, date=dt)
            if trace_list is None:
                break

            if early_stop is True:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '기사 목록 끝에 도달: 종료',
                    'url': url_info['url'] if 'url' in url_info else '',
                    'category': job['category'],
                    'date': dt.strftime('%Y-%m-%d') if dt is not None else '',
                })
                break

            sleep(self.params.sleep)

        return

    def trace_category(self, job: dict) -> None:
        """url_frame 목록을 반복한다."""
        # url 목록 반복
        for url_info in job['list']:
            if len(self.job_sub_category) > 0 and 'category' in url_info and \
                    url_info['category'] not in self.job_sub_category:
                continue

            if url_info['url_frame'].find('date') < 0:
                # page 단위로 크롤링한다.
                self.trace_page(url_info=url_info, job=job, dt=None)
                continue

            # 날짜 지정시
            date_list = list(rrule(DAILY, dtstart=self.date_range['start'], until=self.date_range['end']))

            if self.date_range['step'] < 0:
                date_list = sorted(date_list, reverse=True)

            for dt in date_list:
                date_now = datetime.now(self.timezone)
                if dt > date_now + timedelta(1):
                    break

                # page 단위로 크롤링한다.
                self.trace_page(url_info=url_info, job=job, dt=dt)

        return

    def batch(self) -> None:
        self.params = self.init_arguments()

        self.config = self.open_config(filename=self.params.config)

        self.date_range = self.update_date_range(date_range=self.params.date_range, step=self.params.date_step)
        self.page_range = self.update_page_range(page_range=self.params.page_range, step=self.params.page_step)

        self.job_sub_category = self.params.sub_category.split(',') if self.params.sub_category != '' else []

        # 카테고리 하위 목록을 크롤링한다.
        for job in self.config['jobs']:
            # override elasticsearch config
            job['host'] = os.getenv(
                'ELASTIC_SEARCH_HOST',
                default=job['host'] if 'host' in job else None
            )
            job['index'] = os.getenv(
                'ELASTIC_SEARCH_INDEX',
                default=job['index'] if 'index' in job else None
            )
            job['http_auth'] = os.getenv(
                'ELASTIC_SEARCH_AUTH',
                default=job['http_auth'] if 'http_auth' in job else None
            )

            if 'host' not in job or 'index' not in job:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'elasticsearch 저장 정보 없음',
                    **job
                })
                break

            self.trace_category(job=job)

        return

    @staticmethod
    def init_arguments() -> Namespace:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--overwrite', action='store_true', default=False, help='덮어쓰기')

        # 작업 아이디
        parser.add_argument('--sub-category', default='', help='하위 카테고리')

        parser.add_argument('--date-range', default=None, help='date 날짜 범위: 2000-01-01~2019-04-10')
        parser.add_argument('--date-step', default=-1, type=int, help='date step')

        parser.add_argument('--page-range', default=None, help='page 범위: 1~100')
        parser.add_argument('--page-step', default=1, type=int, help='page step')

        parser.add_argument('--sleep', default=10, type=float, help='sleep time')

        parser.add_argument('--config', default=None, type=str, help='설정 파일 정보')

        parser.add_argument('--update-category-only', action='store_true', default=False, help='category 정보만 업데이트')

        return parser.parse_args()


if __name__ == '__main__':
    WebNewsCrawler().batch()
