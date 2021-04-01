#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from os import getenv
from time import sleep

import pytz
import requests
import urllib3
import yaml
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from dotty_dict import dotty
from jsonfinder import jsonfinder

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.utils.html_parser import HtmlParser
from crawler.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


class WebNewsBase(object):
    """크롤러 베이스"""

    def __init__(self):
        super().__init__()

        self.debug = int(getenv('DEBUG', 0))

        self.job_config = None

        self.parser = HtmlParser()

        self.headers = {
            'mobile': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/89.0.4389.114 Mobile Safari/537.36'
            },
            'desktop': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/89.0.4389.114 Safari/537.36'
            }
        }

        self.sleep_time = 2

        # 후처리 정보
        self.post_process_list = None

        # 로컬 시간 정보
        self.timezone = pytz.timezone('Asia/Seoul')

        # 날짜 범위
        self.date_range = None
        self.page_range = None

        self.start_date = datetime.now(self.timezone)

        # summary
        self.summary = defaultdict(int)

        # ES ENV
        self.elastic_env = {
            'host': getenv('ELASTIC_SEARCH_HOST', default=''),
            'index': getenv('ELASTIC_SEARCH_INDEX', default=''),
            'http_auth': getenv('ELASTIC_SEARCH_AUTH', default=''),
        }

        # params
        self.params: dict or None = None
        self.default_params: dict or None = None

        # logger
        self.logger = Logger()

    def save_article_list(self, item: dict, job: dict, es: ElasticSearchUtils) -> None:
        # 임시 변수 삭제
        for k in ['encoding', 'raw']:
            if k not in item:
                continue
            del item[k]

        item['status'] = 'raw_list'

        self.save_article(es=es, job=job, doc=item, flush=False)

        return

    def get_trace_list(self, html: str, parsing_info: dict = None) -> list:
        """trace tag 목록을 추출해서 반환한다."""
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
                return self.flatten(trace_list=trace_list)

            if parsing['parser'] == 'javascript':
                if isinstance(html, str):
                    soup = BeautifulSoup(html)

                js = [''.join(x.contents) for x in soup.find_all('script') if 'list:' in ''.join(x.contents)][0]

                return [x for _, _, x in jsonfinder(js) if x is not None][0]

        # parser 가 html 인 경우
        soup = self.parser.parse_html(
            html=html,
            parser_type=self.job_config['parsing']['parser'],
        )

        trace_list = []
        self.parser.trace_tag(
            soup=soup,
            index=0,
            result=trace_list,
            tag_list=self.job_config['parsing']['trace'],
        )

        return trace_list

    def get_article_body(self, item: dict, offline: bool = False) -> str:
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

    def save_article(self, doc: dict, es: ElasticSearchUtils, job: dict, html: str = None,
                     article: dict = None, flush: bool = True) -> dict:
        """크롤링한 문서를 저장한다."""
        # 후처리
        doc = self.parser.merge_values(item=doc)

        if article:
            article = self.parser.merge_values(item=article)

            # json merge
            if 'json' in doc and 'json' in article:
                m_json = {
                    **json.loads(doc['json']),
                    **json.loads(article['json'])
                }

                del doc['json']
                article['json'] = json.dumps(m_json)

            if 'raw' in article and len(article['raw']) != 0:
                doc.update(article)
            elif 'json' in article and len(article['json']) != 0:
                doc.update(article)
            else:
                # 파싱 에러 처리
                if 'raw' not in doc or doc['raw'] == '':
                    doc['raw'] = str(html)

                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '[COLUMN_ERROR] html, json, raw 필드가 없음',
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
                'message': '[COLUMN_ERROR] doc_id 가 없음. 저장하지 않음',
                'url': doc['url'],
                **doc
            })
            return doc

        doc_id = doc['_id']

        es.save_document(document=doc, delete=False)

        if article:
            self.summary['new_article'] += 1
        else:
            self.summary['new_list'] += 1

            if self.params['verbose'] == 1:
                dt_str = doc['date'] if isinstance(doc['date'], str) else doc[
                    'date'].isoformat() if 'date' in doc else ''

                self.logger.log(
                    msg={
                        'level': 'MESSAGE',
                        'message': '저장 성공',
                        'category': '[' + ']['.join([job[x] for x in ['name', 'category'] if x in job]) + ']',
                        '_id': doc_id,
                        'date': dt_str.split('T')[0],
                        'title': doc['title'],
                        'url': doc['url'],
                        'doc_url': es.get_doc_url(document_id=doc_id),
                    },
                    show_date=False
                )

        if flush is False:
            return doc

        flag = es.flush()

        # 성공 로그 표시
        if flag is True:
            dt_str = doc['date'] if isinstance(doc['date'], str) else doc['date'].isoformat() if 'date' in doc else ''

            self.logger.log(
                msg={
                    'level': 'MESSAGE',
                    'message': '저장 성공',
                    'category': '-'.join([job[x] for x in ['name', 'category'] if x in job]),
                    '_id': doc_id,
                    'date': dt_str.split('T')[0],
                    'title': doc['title'],
                    'url': doc['url'],
                    'doc_url': es.get_doc_url(document_id=doc_id),
                },
                show_date=False
            )

        return doc

    @staticmethod
    def merge_category(doc: dict, es: ElasticSearchUtils) -> dict:
        """category 정보를 병합한다."""
        if 'category' not in doc:
            return doc

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

    def is_within_date_range(self, doc: dict, query: dict) -> bool:
        if self.params['date_range'] is None or self.params['date_range'] not in {'today'}:
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
                    'message': '[DATE_ERROR]날짜 변환 오류',
                    'date': doc['date'],
                    'exception': str(e),
                })
                return True

        today = datetime.now(self.timezone)
        if dt.strftime('%Y%m%d') != today.strftime('%Y%m%d'):
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '[DATE_ERROR] 날짜 범위 넘어감',
                'date': dt.strftime('%Y-%m-%d'),
                'today': today.strftime('%Y-%m-%d'),
            })
            return False

        return True

    def is_skip(self, es: ElasticSearchUtils, date: datetime, job: dict, url: str, doc_id: str) -> (bool, str):
        if self.params['overwrite'] is True:
            return False, None

        es.index = es.get_target_index(
            tag=es.get_index_year_tag(date=date),
            index=job['index'],
        )

        is_skip, doc_index = self.is_doc_exists(
            url=url,
            index=job['index_group'] if 'index_group' in job else job['index'].replace('-{year}', '*'),
            doc_id=doc_id,
            es=es,
        )
        if is_skip is True:
            if self.params['verbose'] == 1:
                self.logger.log(msg={
                    'level': 'INFO',
                    'message': '[DOC_EXISTS] 크롤링된 문서가 있음',
                    'doc_id': doc_id,
                    'url': url,
                    'doc_url': es.get_doc_url(document_id=doc_id)
                })

            return True, doc_index

        return False, doc_index

    def masking_auth(self, obj: dict) -> None:
        for k, v in obj.items():
            if isinstance(v, dict):
                self.masking_auth(obj=v)
            elif k.find('auth') >= 0:
                obj[k] = '*****'

        return

    def show_summary(self, tag: str, es: ElasticSearchUtils = None) -> None:
        finished = datetime.now(self.timezone)
        runtime = finished - self.start_date

        summary = {
            'tag': tag,
            'start': self.start_date.isoformat(),
            'runtime': f'{runtime.total_seconds():0.2f}',
            'finished': finished.isoformat(),
            'params': {
                **self.params
            },
            **self.summary,
        }
        self.masking_auth(obj=summary)

        self.logger.log(msg={'level': 'SUMMARY', **summary})

        if es:
            es.save_summary(index='crawler-summary', summary=summary)

        return

    def remove_empty_date(self, doc: dict) -> None:
        """날짜 필드를 확인해서 날짜 파싱 오류일 경우, 날짜 필드를 삭제한다."""
        if 'date' not in doc:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '[DATE_ERROR] date 필드가 없습니다.',
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
                    'message': '[DATE_ERROR] 날짜 파싱 에러: date 필드 삭제',
                    'exception': str(e),
                    'date': doc['date'],
                })

                del doc['date']
                return

        return

    def parse_tag(self, resp, url_info: dict, parsing_info: list, base_url: str,
                  default_date: datetime = None) -> dict or None:
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
            parser_version = self.job_config['parsing']['version'] if 'version' in self.job_config['parsing'] else None
            item = self.parser.parse(
                html=None,
                soup=resp,
                base_url=base_url,
                parsing_info=parsing_info,
                default_date=default_date,
                parser_version=parser_version,
            )

        # url 추출
        if 'url' in item and isinstance(item['url'], list):
            if len(item['url']) > 0:
                item['url'] = item['url'][0]
            else:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '[PARING_ERROR] trace tag에서 url 추출 에러',
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
                'message': '[PARING_ERROR] HTML 파싱 에러',
                'resp': str(resp)[:200] + ' ...',
                'text': text,
                'url': url_info['url'],
            })

            return None

        return item

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
            if self.params['overwrite'] is False and len(q) == 0:
                if self.params['verbose'] == 1:
                    self.logger.log(msg={
                        'level': 'INFO',
                        'message': 'query 필드가 없음',
                        'url': url,
                    })

                return None

            try:
                result = id_frame['frame'].format(**q)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '[CONFIG_ERROR] url fame 에러',
                    'q': q,
                    'id_frame': id_frame['frame'],
                    'exception': str(e),
                })
        elif id_frame['type'] == 'value':
            result = id_frame['frame'].format(**item)

        return result.strip()

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

    @staticmethod
    def simplify(doc: list or dict, size: int = 30) -> list or dict:
        if isinstance(doc, dict) is False:
            return str(doc)[:size] + ' ...'

        result = {}
        for col in doc:
            result[col] = str(doc[col])[:size] + ' ...'

        return result

    @staticmethod
    def merge_params(job: dict, params: dict, default_params: dict) -> (dict, dict):
        # override elasticsearch config
        job['host'] = getenv(
            'ELASTIC_SEARCH_HOST',
            default=job['host'] if 'host' in job else None
        )
        job['index'] = getenv(
            'ELASTIC_SEARCH_INDEX',
            default=job['index'] if 'index' in job else None
        )
        job['http_auth'] = getenv(
            'ELASTIC_SEARCH_AUTH',
            default=job['http_auth'] if 'http_auth' in job else None
        )

        # merge config args
        args = job['args'] if 'args' in job else None
        if args is None:
            return params, job

        for col, val in args.items():
            if col not in default_params or col not in params:
                continue

            if default_params[col] != params[col]:
                continue

            if isinstance(default_params[col], int):
                val = int(val)

            params[col] = val

        return params, job

    @staticmethod
    def flatten(trace_list: list) -> list:
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

    @staticmethod
    def open_config(filename: str) -> list:
        file_list = filename.split(',')

        result = []
        for f_name in file_list:
            with open(f_name, 'r') as fp:
                data = yaml.load(stream=fp, Loader=yaml.FullLoader)
                result.append(dict(data))

        return result

    def update_page_range(self, page_range: str = None, step: int = 1) -> dict:
        """페이지 범위를 갱신한다."""
        if isinstance(step, str):
            step = int(step)

        result = {
            'start': 1,
            'end': 900,
            'step': step
        }

        self.params.update({
            'start_page': result['start'],
            'end_page': result['end'],
        })

        if page_range is None:
            return result

        pg_start, pg_end = page_range.split('~', maxsplit=1)

        result = {
            'start': int(pg_start),
            'end': int(pg_end),
            'step': step
        }

        self.params.update({
            'start_page': result['start'],
            'end_page': result['end'],
        })

        return result

    def update_date_range(self, date_range: str = None, step: int = 1) -> dict:
        """날짜 범위를 갱신한다."""
        if isinstance(step, str):
            step = int(step)

        today = datetime.now(self.timezone)
        result = {
            'end': today,
            'start': today,
            'step': step,
        }

        self.params.update({
            'start_date': result['start'],
            'end_date': result['end'],
        })

        if date_range is None:
            return result

        # today
        if date_range == 'today':
            return result

        # 3days
        if date_range.find('d') > 0:
            n: str = date_range.split('d')[0].strip()

            if n.isdigit():
                result['end'] += relativedelta(days=-int(n))

                self.params.update({
                    'start_date': result['start'],
                    'end_date': result['end'],
                })
                return result

        # 날자 범위 추출
        token = date_range.split('~', maxsplit=1)

        # 2021-01 은 2021-01-13 으로 변환됨
        dt_start = parse_date(token[0]).astimezone(self.timezone)

        # 2021-01-01 인 경우
        dt_end = dt_start + relativedelta(months=1)

        if len(token) > 1:
            dt_end = parse_date(token[1]).astimezone(self.timezone)

        result = {
            'end': max(dt_start, dt_end),
            'start': min(dt_start, dt_end),
            'step': step,
        }

        today = datetime.now(self.timezone)
        if result['end'] > today:
            result['end'] = today

        self.params.update({
            'start_date': result['start'],
            'end_date': result['end'],
        })

        return result

    def get_post_page(self, url_info: dict) -> None or str:
        headers = self.headers['desktop']
        if 'headers' in url_info:
            headers.update({
                'Content-Type': 'application/json'
            })

        if 'url' not in url_info:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '[CONFIG_ERROR] url 정보가 없음',
                **url_info,
            })

            return None

        # 페이지 조회
        try:
            resp = requests.post(
                url=url_info['url'],
                verify=False,
                timeout=60,
                headers=headers,
                json=url_info['post_data'],
                allow_redirects=True,
            )
        except Exception as e:
            sleep_time = 10

            self.logger.error(msg={
                'level': 'ERROR',
                'message': '[REQUESTS_ERROR] html 페이지 조회 에러',
                'sleep_time': sleep_time,
                'exception': str(e),
                **url_info,
            })

            sleep(sleep_time)
            return None

        # 상태 코드 확인
        status_code = resp.status_code
        if status_code // 100 != 2:
            sleep_time = 10

            self.logger.error(msg={
                'level': 'ERROR',
                'message': '[REQUESTS_ERROR] url 조회 상태 코드 에러',
                'sleep_time': sleep_time,
                'status_code': status_code,
                **url_info,
            })

            sleep(sleep_time)
            return None

        return resp.json()

    def get_html_page(self, url_info: dict, log_msg: dict = None) -> None or str:
        """웹 문서를 조회한다."""
        log_msg = log_msg if log_msg is not None else {}

        headers = self.headers['desktop']
        if 'headers' in url_info:
            headers.update(url_info['headers'])

        if 'url' not in url_info:
            self.logger.error(msg={
                **log_msg,
                'level': 'ERROR',
                'message': '[CONFIG_ERROR] url 정보가 없음',
                **url_info,
            })

            return None

        # 페이지 조회
        try:
            resp = requests.get(
                url=url_info['url'],
                verify=False,
                timeout=60,
                headers=headers,
                allow_redirects=True,
            )
        except Exception as e:
            sleep_time = 10

            self.logger.error(msg={
                **log_msg,
                'level': 'ERROR',
                'message': '[REQUESTS_ERROR] html 페이지 조회 에러',
                'sleep_time': sleep_time,
                'exception': str(e),
                **url_info,
            })

            sleep(sleep_time)
            return None

        # 상태 코드 확인
        status_code = resp.status_code
        if status_code // 100 != 2:
            sleep_time = 10

            self.logger.error(msg={
                **log_msg,
                'level': 'ERROR',
                'message': '[REQUESTS_ERROR] url 조회 상태 코드 에러',
                'sleep_time': sleep_time,
                'status_code': status_code,
                **url_info,
            })

            sleep(sleep_time)
            return None

        # 인코딩 변환이 지정되어 있은 경우 인코딩을 변경함
        encoding = url_info['encoding'] if 'encoding' in url_info else None

        result = resp.text.strip()
        if encoding is None:
            soup, encoding = self.parser.get_encoding_type(html_body=result)

        if encoding is not None:
            result = resp.content.decode(encoding, 'ignore').strip()

        return result

    def get_dict_value(self, data: list or dict, key_list: list, result: list) -> None:
        """commentlist.list 형태의 키 값을 찾아서 반환한다."""
        if len(key_list) == 0:
            if isinstance(data, list):
                result += data
            else:
                result.append(data)
            return

        if isinstance(data, list):
            for item in data:
                self.get_dict_value(data=item, key_list=key_list, result=result)
        elif isinstance(data, dict):
            k = key_list[0]
            if k in data:
                self.get_dict_value(data=data[k], key_list=key_list[1:], result=result)

        return

    @staticmethod
    def doc_exists(index: str, doc_id: str, es: ElasticSearchUtils) -> (bool, str):
        resp = es.conn.search(
            index=index,
            _source=['url', 'raw'],
            body={
                'query': {
                    'ids': {
                        'values': [doc_id]
                    }
                }
            }
        )

        if resp['hits']['total']['value'] == 0:
            return False, None

        for item in resp['hits']['hits']:
            if 'raw' not in item['_source']:
                return False, item['_index']

            if item['_source']['raw'] != '':
                return True, item['_index']

        return False, None

    def is_doc_exists(self, doc_id: str, es: ElasticSearchUtils, url: str, index: str,
                      reply_info: dict = None) -> (bool, str):
        """문서 아이디를 이전 기록과 비교한다."""
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-ids-query.html

        # 문서가 있는지 조회
        is_exists, doc_index = self.doc_exists(index=index, doc_id=doc_id, es=es)

        if is_exists is False:
            return False, doc_index

        # 댓글 정보 추가 확인
        if reply_info is not None:
            field_name = reply_info['source']
            doc = es.conn.get(
                id=doc_id,
                index=index,
                _source=[field_name],
            )['_source']

            if field_name not in doc:
                return False, None

            if doc[field_name] != reply_info['count']:
                return False, None

        if self.params['verbose'] == 1:
            self.logger.log(msg={
                'level': 'INFO',
                'message': '문서가 존재함, 건너뜀',
                'doc_id': doc_id,
                'url': url,
                'doc_url': es.get_doc_url(document_id=doc_id)
            })

        return True, None
