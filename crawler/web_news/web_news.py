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
from jsonfinder import jsonfinder

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.web_news.base import WebNewsBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class WebNewsCrawler(WebNewsBase):
    """웹 뉴스 크롤러"""

    def __init__(self):
        super().__init__()

        self.params: Namespace or None = None

        self.trace_depth: int = 0

        self.update_date: bool = False

        self.job_names: set or None = None
        self.job_sub_category: set or None = None

        self.summary = {
            'start': datetime.now(self.timezone),
            'finished': datetime.now(self.timezone),
            'skip': 0,
            'page': 0,
            'list': 0,
            'article': 0,
        }

        self.elastic_env = {
            'host': os.getenv('ELASTIC_SEARCH_HOST', default=''),
            'index': os.getenv('ELASTIC_SEARCH_INDEX', default=''),
            'http_auth': os.getenv('ELASTIC_SEARCH_AUTH', default=''),
        }

    def open_elasticsearch(self, date: datetime, job: dict, mapping: str = None) -> ElasticSearchUtils:
        """디비에 연결한다."""
        index_tag = None
        if date is not None:
            index_tag = date.year

        if mapping is None and 'index_mapping' in self.job_config:
            mapping: dict = self.job_config['index_mapping']

        return ElasticSearchUtils(
            tag=index_tag,
            host=job['host'],
            index=None,
            bulk_size=20,
            http_auth=job['http_auth'],
            mapping=mapping,
        )

    def get_article_page(self, item: dict, offline: bool = False) -> str:
        """기사 본문을 조회한다."""
        resp = None
        if offline is True:
            if 'raw' in item:
                resp = item['raw']
            elif 'html' in item:
                resp = item['html']
            elif 'json' in item:
                resp = item['json']
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

    def remove_empty_date(self, doc: dict) -> None:
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

    def save_article(self, doc: dict, es: ElasticSearchUtils, job: dict, html: str = None,
                     article: dict = None, flush: bool = True) -> dict:
        """크롤링한 문서를 저장한다."""
        # 후처리
        doc = self.parser.merge_values(item=doc)

        if article is not None:
            article = self.parser.merge_values(item=article)

            # json merge
            if 'json' in doc and 'json' in article:
                m_json = {
                    **json.loads(doc['json']),
                    **json.loads(article['json'])
                }

                del doc['json']
                article['json'] = json.dumps(m_json)

            # 파싱 에러 처리
            if 'raw' in article and len(article['raw']) != 0:
                doc.update(article)
            elif 'json' in article and len(article['json']) != 0:
                doc.update(article)
            else:
                if 'raw' not in doc or doc['raw'] == '':
                    doc['raw'] = str(html)

                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'html, json, raw 필드가 없음',
                    'url': doc['url'],
                })

        # 날짜 필드 오류 처리
        self.remove_empty_date(doc=doc)

        # 인덱스 변경
        if 'date' in doc:
            es.index = es.get_target_index(
                tag=es.get_index_year_tag(date=doc['date']),
                index=job['index'],
            )

        # category 필드 병합
        doc = self.merge_category(doc=doc, es=es)

        # 문서 저장
        if '_id' not in doc:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'doc_id 가 없음. 저장하지 않음',
                'url': doc['url'],
                **doc
            })
            return doc

        doc_id = doc['_id']

        es.save_document(document=doc, delete=False)
        self.cache.set(key=doc_id, value=True)

        if flush is False:
            return doc

        flag = es.flush()

        # 성공 로그 표시
        if flag is True:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '기사 저장 성공',
                '_id': doc_id,
                'url': doc['url'],
                'doc_url': es.get_doc_url(document_id=doc_id),
                **{x: doc[x] for x in ['date', 'title'] if x in doc},
            })

        return doc

    @staticmethod
    def merge_category(doc: dict, es: ElasticSearchUtils) -> dict:
        """category 정보를 병합한다."""
        doc_id = None

        if '_id' in doc:
            doc_id = doc['_id']
        elif 'document_id' in doc:
            doc_id = doc['document_id']

        if doc_id is None:
            return doc

        resp = es.conn.mget(
            body={
                'docs': [{'_id': doc_id}]
            },
            index=es.index,
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

    def get_trace_list(self, html: str, parsing_info: dict = None) -> list or None:
        """trace tag 목록을 추출해서 반환한다."""
        trace_list = []
        if len(parsing_info) > 0 and 'parser' in parsing_info[0]:
            parsing = parsing_info[0]

            soup = html
            if parsing['parser'] == 'json':
                if isinstance(html, str):
                    soup = json.loads(html)

                column = parsing['column']
                if column == '*':
                    soup = {
                        '*': soup
                    }

                dot = dotty(soup)

                trace_list = list(dot[column]) if column in dot else []
                trace_list = self.flatten(trace_list=trace_list)
            elif parsing['parser'] == 'javascript':
                if isinstance(html, str):
                    soup = BeautifulSoup(html)

                js = [''.join(x.contents) for x in soup.find_all('script') if 'list:' in ''.join(x.contents)][0]

                trace_list = [x for _, _, x in jsonfinder(js) if x is not None][0]
        else:
            soup = self.parser.parse_html(
                html=html,
                parser_type=self.job_config['parsing']['parser'],
            )

            self.parser.trace_tag(
                soup=soup,
                index=0,
                result=trace_list,
                tag_list=self.job_config['parsing']['trace'],
            )

        if len(trace_list) == 0:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'trace_list 가 없음',
                'trace_size': len(trace_list),
                'sleep_time': self.params.sleep,
            })

            sleep(self.params.sleep)
            return None

        return trace_list

    def parse_tag(self, resp, url_info: dict, parsing_info: list, base_url: str):
        """trace tag 하나를 파싱해서 반환한다."""
        # json 인 경우 맵핑값 매칭
        first_item = deepcopy(parsing_info[0]) if len(parsing_info) > 0 else {}
        if 'mapping' in url_info:
            if 'mapping' not in first_item:
                first_item['mapping'] = {}

            first_item['mapping'].update(url_info['mapping'])

        if 'parser' in first_item and first_item['parser'] == 'json':
            if isinstance(resp, str):
                resp = json.loads(resp)

            item = self.parser.parse_json(resp=resp, mapping_info=first_item['mapping'])
        else:
            if isinstance(resp, str) or isinstance(resp, bytes):
                resp = self.parser.parse_html(
                    html=resp,
                    parser_type=self.job_config['parsing']['parser'],
                )

            # 목록에서 기사 본문 링크 추출
            item = self.parser.parse(
                html=None,
                soup=resp,
                base_url=base_url,
                parsing_info=parsing_info,
                parser_version=self.job_config['parsing']['version'] if 'version' in self.job_config[
                    'parsing'] else None,
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
                soup = BeautifulSoup(resp, 'html5lib')
                text = ''.join(x.get_text() for x in soup.find_all())

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
                'resp': str(resp)[:200] + ' ...',
                'text': text,
                'url': url_info['url'],
            })

            return None

        return item

    def is_skip(self, es: ElasticSearchUtils, date: datetime, job: dict, url: str, doc_id: str) -> (bool, str):
        if self.params.overwrite is True:
            return False, None

        es.index = es.get_target_index(
            tag=es.get_index_year_tag(date=date),
            index=job['index'],
        )

        is_skip, doc_index = self.check_doc_id(
            url=url,
            index=job['index_group'] if 'index_group' in job else job['index'].replace('-{year}', '*'),
            doc_id=doc_id,
            es=es,
        )
        if is_skip is True:
            self.logger.info(msg={
                'level': 'INFO',
                'message': '크롤링된 뉴스가 있음',
                'doc_id': doc_id,
                'url': url,
                'doc_url': es.get_doc_url(document_id=doc_id)
            })

            return True, doc_index

        return False, doc_index

    def trace_next_page(self, html: str, url_info: dict, job: dict, date: datetime, es: ElasticSearchUtils,
                        query: dict) -> None:
        """다음 페이지를 따라간다."""
        if 'trace_next_page' not in self.job_config['parsing']:
            return

        # html 이 json 인 경우
        if isinstance(html, dict) or isinstance(html, list):
            return

        trace_tag = self.job_config['parsing']['trace_next_page']

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
            parser_type=self.job_config['parsing']['parser'],
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

            next_url = self.job_config['parsing']
            next_url['url'] = url

            resp = self.get_html_page(url_info=self.job_config['parsing'])
            if resp is None:
                continue

            self.logger.info(msg={
                'level': 'INFO',
                'message': '다음페이지 크롤링: 슬립',
                'sleep_time': self.params.sleep,
            })

            sleep(self.params.sleep)

            early_stop = self.trace_news(html=resp, url_info=url_info, job=job, date=date, es=es, query=query)
            if early_stop is True:
                break

        return

    def check_date_range(self, doc: dict, query: dict) -> bool:
        if self.params.date_range is None or self.params.date_range not in {'today'}:
            return True

        if 'date' not in doc:
            return True

        if 'page' in query and query['page'] < 3:
            return True

        dt = doc['date']
        if isinstance(doc['date'], str):
            try:
                dt = parse_date(doc['date'])
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '날짜 변환 오류',
                    'date': doc['date'],
                    'exception': str(e),
                })
                return True

        today = datetime.now(self.timezone)
        if dt.strftime('%Y%m%d') != today.strftime('%Y%m%d'):
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '날짜 범위 넘어감',
                'date': dt.strftime('%Y-%m-%d'),
                'today': today.strftime('%Y-%m-%d'),
            })
            return False

        return True

    def trace_news(self, html: str, url_info: dict, job: dict, date: datetime, es: ElasticSearchUtils,
                   query: dict) -> bool:
        """개별 뉴스를 따라간다."""
        # 기사 목록을 추출한다.
        trace_list = self.get_trace_list(html=html, parsing_info=self.job_config['parsing']['trace'])
        if self.params.verbose == 0:
            self.logger.log(msg={'CONFIG_DEBUG': 'trace_list', 'trace_list': self.simplify(trace_list)})
            sleep(self.params.sleep)

        if trace_list is None:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'trace_list 가 없음: 조기 종료',
                **url_info
            })
            return True

        # 베이스 url 추출
        base_url = self.parser.parse_url(url_info['url'])[1]

        is_date_range_stop = False

        # 개별 뉴스를 따라간다.
        for trace in trace_list:
            item = self.parse_tag(
                resp=trace,
                url_info=url_info,
                base_url=base_url,
                parsing_info=self.job_config['parsing']['list'],
            )

            self.summary['list'] += 1

            if self.params.verbose == 0:
                self.logger.log(msg={
                    'CONFIG_DEBUG': 'list info',
                    'trace': self.simplify(trace),
                    'item': self.simplify(item)
                })
                sleep(self.params.sleep)

            if item is None or 'url' not in item:
                continue

            item['url'] = urljoin(base_url, item['url'])
            item['category'] = job['category']
            item['encoding'] = url_info['encoding'] if 'encoding' in url_info else None

            if date is None and 'date' in item:
                date = item['date']

            if self.check_date_range(doc=item, query=query) is False:
                is_date_range_stop = True
                break

            # 기존 크롤링된 문서를 확인한다.
            doc_id = self.get_doc_id(url=item['url'], job=job, item=item)

            if self.params.verbose == 0:
                self.logger.log(msg={'CONFIG_DEBUG': 'document id', 'doc_id': doc_id})
                sleep(self.params.sleep)

            if doc_id is None:
                continue

            item['_id'] = doc_id

            is_skip, doc_index = self.is_skip(es=es, date=date, job=job, url=item['url'], doc_id=doc_id)
            if is_skip is True:
                continue

            # 기사 목록 저장
            if self.params.list:
                # 임시 변수 삭제
                for k in ['encoding', 'raw']:
                    if k not in item:
                        continue
                    del item[k]

                item['status'] = 'raw_list'

                if self.params.verbose == 1:
                    self.logger.log(
                        msg={
                            'category': '-'.join([job[x] for x in ['name', 'category'] if x in job]),
                            '_id': item['_id'],
                            'date': item['date'].isoformat().split('T')[0],
                            'title': item['title']
                        },
                        show_date=False
                    )

                self.save_article(es=es, job=job, doc=item, flush=False)
                continue

            # 기사 본문 조회
            article_html = self.get_article_page(item=item, offline=False)

            # 문서 저장
            article = self.parse_tag(
                resp=article_html,
                url_info=item,
                base_url=item['url'],
                parsing_info=self.job_config['parsing']['article'],
            )

            self.summary['article'] += 1

            if self.params.verbose == 0:
                self.logger.log(msg={'CONFIG_DEBUG': 'article', 'article': self.simplify(article)})
                sleep(self.params.sleep)

            # 임시 변수 삭제
            if 'encoding' in item:
                del item['encoding']

            if article is None or len(article) == 0:
                continue

            article['_id'] = doc_id

            # 댓글 post process 처리
            self.post_request(article=article, job=job, item=item)

            item['status'] = 'article'

            # 기사 저장
            self.save_article(
                es=es,
                job=job,
                doc=item,
                html=article_html,
                article=article,
            )

            self.logger.info(msg={
                'level': 'INFO',
                'message': '뉴스 본문 크롤링: 슬립',
                'sleep_time': self.params.sleep,
            })
            sleep(self.params.sleep)

        if self.params.list:
            es.flush()

        # 다음 페이지 정보가 있는 경우
        self.trace_next_page(html=html, url_info=url_info, job=job, date=date, es=es, query=query)

        # 날짜 범위 점검
        if is_date_range_stop is True:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '날짜 범위 넘어감: 조기 종료',
            })
            return True

        return False

    def trace_page(self, url_info: dict, job: dict, dt: datetime = None) -> None:
        """뉴스 목록을 크롤링한다."""
        self.trace_depth = 0

        self.cache.clear()
        self.skip_count = 0

        # 디비에 연결한다.
        es = self.open_elasticsearch(date=dt, job=job, mapping=self.params.mapping)

        # start 부터 end 까지 반복한다.
        for page in range(self.page_range['start'], self.page_range['end'] + 1, self.page_range['step']):
            # 쿼리 url 생성
            q = dict(page=page)
            if dt is not None and 'date_format' in url_info:
                q['date'] = dt.strftime(url_info['date_format'])

            url_info['url'] = url_info['url_frame'].format(**q)

            if 'category' in url_info:
                job['category'] = url_info['category']

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '뉴스 목록 크롤링',
                'job_name': job['name'] if 'name' in job else '',
                'url': url_info['url'] if 'url' in url_info else '',
                'query': q,
                'date': dt.strftime('%Y-%m-%d') if dt is not None else '',
                'skip_count': self.skip_count,
            })

            # 기사 목록 조회
            resp = self.get_html_page(url_info=url_info, log_msg={'trace': '뉴스 목록 조회'})
            self.summary['page'] += 1

            if self.params.verbose == 0:
                self.logger.log(msg={'CONFIG_DEBUG': 'list page', 'url': url_info['url']})
                sleep(self.params.sleep)

            if resp is None:
                continue

            prev_skip_count = self.skip_count
            self.summary['skip'] += self.skip_count

            # 문서 저장
            early_stop = self.trace_news(html=resp, url_info=url_info, job=job, date=dt, es=es, query=q)
            if early_stop is True:
                break

            # 중복 문서 개수 점검
            if 0 < prev_skip_count < self.skip_count:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '마지막 페이지: 종료',
                    'skip_count': f'{self.skip_count} > {prev_skip_count}',
                    **url_info
                })
                break

            sleep(self.params.sleep)

        return

    def trace_category(self, job: dict) -> None:
        """url_frame 목록을 반복한다."""
        # url 목록 반복
        for url_info in job['list']:
            if self.job_sub_category is not None and 'category' in url_info and \
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

    def trace_job(self, job: dict) -> None:
        if 'name' in job and self.job_names is not None:
            if job['name'] not in self.job_names:
                return

        # override args config
        if 'args' not in job:
            job['args'] = {}

        self.date_range = self.update_date_range(
            date_range=self.params.date_range,
            step=self.params.date_step,
            args=job['args']
        )

        self.page_range = self.update_page_range(
            page_range=self.params.page_range,
            step=self.params.page_step,
            args=job['args']
        )

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '날짜와 페이지 범위',
            'date_range': {k: str(v) for k, v in self.date_range.items()},
            'page_range': self.page_range,
        })

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
            })
            return

        self.trace_category(job=job)

        return

    def running_state(self, tag: str) -> None:
        self.summary['finished'] = datetime.now(self.timezone)

        self.summary['runtime'] = self.summary['finished'] - self.summary['start']

        self.logger.log(msg={
            'level': 'SUMMARY',
            'args': vars(self.params),
            'env': self.elastic_env,
            'tag': tag,
            **self.summary
        })
        return

    def batch(self) -> None:
        """ job -> category -> date -> page 순서 """
        self.params = self.init_arguments()

        config_list = self.open_config(filename=self.params.config)

        self.job_names = set(self.params.job_name.split(',')) if self.params.job_name != '' else None
        self.job_sub_category = set(self.params.sub_category.split(',')) if self.params.sub_category != '' else None

        # 카테고리 하위 목록을 크롤링한다.
        for self.job_config in config_list:
            for job in self.job_config['jobs']:
                self.trace_job(job=job)

                self.running_state(tag='job done')

        self.running_state(tag='completed')

        return

    @staticmethod
    def init_arguments() -> Namespace:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--job-name', default='', type=str, help='잡 이름, 없는 경우 전체')

        parser.add_argument('--overwrite', action='store_true', default=False, help='덮어쓰기')

        parser.add_argument('--list', action='store_true', default=False, help='기사 목록 크롤링')
        parser.add_argument('--article', action='store_true', default=False, help='TODO: 기사 본문 크롤링')
        parser.add_argument('--pipeline', default='', type=str, help='TODO: pipeline')

        parser.add_argument('--verbose', default=-1, type=int, help='verbose 모드: 0=config, 1=list info')

        parser.add_argument('--sub-category', default='', type=str, help='하위 카테고리')

        parser.add_argument('--date-range', default=None, type=str, help='date 날짜 범위: 2000-01-01~2019-04-10')
        parser.add_argument('--date-step', default=-1, type=int, help='date step')

        parser.add_argument('--page-range', default=None, type=str, help='page 범위: 1~100')
        parser.add_argument('--page-step', default=1, type=int, help='page step')

        parser.add_argument('--sleep', default=10, type=float, help='sleep time')

        parser.add_argument('--config', default=None, type=str, help='설정 파일 정보')
        parser.add_argument('--mapping', default=None, type=str, help='인덱스 맵핑 파일 정보')

        return parser.parse_args()


if __name__ == '__main__':
    WebNewsCrawler().batch()
