#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
from os import getenv
from time import sleep

import pytz
import requests
import urllib3
import yaml
from cachelib import SimpleCache
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

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

        self.config = None

        self.parser = HtmlParser()

        self.headers = {
            'mobile': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                              'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                              'Version/11.0 Mobile/15A372 Safari/604.1'
            },
            'desktop': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/87.0.4280.141 Safari/537.36'
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

        self.cache = SimpleCache()

        self.logger = Logger()

    @staticmethod
    def open_config(filename: str) -> dict:
        with open(filename, 'r') as fp:
            data = yaml.load(stream=fp, Loader=yaml.FullLoader)
            return dict(data)

    @staticmethod
    def update_page_range(page_range: str = None, step: int = 1) -> dict:
        """페이지 범위를 갱신한다."""
        result = {
            'start': 1,
            'end': 900,
            'step': step
        }

        if page_range is None:
            return result

        pg_start, pg_end = page_range.split('~', maxsplit=1)
        return {
            'start': int(pg_start),
            'end': int(pg_end),
            'step': step
        }

    def update_date_range(self, date_range: str = None, step: int = 1) -> dict:
        """날짜 범위를 갱신한다."""
        today = datetime.now(self.timezone)
        result = {
            'end': today,
            'start': today,
            'step': step,
        }

        if date_range is None:
            return result

        token = date_range.split('~', maxsplit=1)

        dt_start = parse_date(token[0])
        dt_end = dt_start + relativedelta(months=1)

        if len(token) > 1:
            dt_end = parse_date(token[1])

        result = {
            'end': self.timezone.localize(dt_end),
            'start': self.timezone.localize(dt_start),
            'step': step,
        }

        today = datetime.now(self.timezone)
        if result['end'] > today:
            result['end'] = today

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
                'message': 'url 정보가 없음',
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
                'message': 'html 페이지 조회 에러',
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
                'message': 'url 조회 상태 코드 에러',
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
                'message': 'url 정보가 없음',
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
                'message': 'html 페이지 조회 에러',
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
                'message': 'url 조회 상태 코드 에러',
                'sleep_time': sleep_time,
                'status_code': status_code,
                **url_info,
            })

            sleep(sleep_time)
            return None

        # if 'parser' in url_info and url_info['parser'] == 'json':
        #     try:
        #         return resp.json()
        #     except Exception as e:
        #         self.logger.error(msg={
        #             **log_msg,
        #             'level': 'ERROR',
        #             'message': 'json 파싱 에러',
        #             'e': str(e),
        #             'resp': str(resp.content),
        #         })
        #         return None

        # 인코딩 변환이 지정되어 있은 경우 인코딩을 변경함
        encoding = None

        result = resp.text.strip()
        if encoding is None:
            soup, encoding = self.parser.get_encoding_type(html_body=result)

        if encoding is not None:
            result = resp.content.decode(encoding, 'ignore').strip()

        return result

    def set_history(self, value: set, name: str) -> None:
        """문서 아이디 이력을 저장한다."""
        self.cache.set(name, value, timeout=600)
        return

    def get_history(self, name: str, default: set) -> set:
        """문서 아이디 이력을 반환한다."""
        value = self.cache.get(name)

        if value is None:
            value = default
            self.cache.set(name, value, timeout=600)

        return value

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

    def check_doc_id(self, doc_id: str, es: ElasticSearchUtils, url: str, index: str, doc_history: set,
                     reply_info: dict = None) -> bool:
        """문서 아이디를 이전 기록과 비교한다."""
        # 캐쉬에 저장된 문서가 있는지 조회
        if doc_id in doc_history:
            self.logger.info(msg={
                'level': 'INFO',
                'message': '중복 문서, 건너뜀',
                'doc_id': doc_id,
                'url': url,
            })
            return True

        # 문서가 있는지 조회
        is_exists = es.conn.exists(index=index, id=doc_id)
        if is_exists is False:
            return False

        # html 필드가 있는지 조회
        doc = es.conn.get(index=index, id=doc_id, _source=['html'])
        if 'html' not in doc['_source']:
            return False

        # 댓글 정보 추가 확인
        if reply_info is not None:
            field_name = reply_info['source']
            doc = es.conn.get(
                id=doc_id,
                index=index,
                _source=[field_name],
            )['_source']

            if field_name not in doc:
                return False

            if doc[field_name] != reply_info['count']:
                return False

        doc_history.add(doc_id)

        self.logger.info(msg={
            'level': 'INFO',
            'message': 'elasticsearch 에 존재함, 건너뜀',
            'doc_id': doc_id,
            'url': url,
            'doc_url': es.get_doc_url(document_id=doc_id)
        })

        return True
