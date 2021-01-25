#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from datetime import datetime
from os import getenv
from time import sleep

import pytz
import requests
import urllib3
import yaml
from cachelib import SimpleCache

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.utils.html_parser import HtmlParser
from crawler.utils.logger import Logger
from crawler.web_news.post_process import PostProcessUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class WebNewsBase(object):
    """크롤러 베이스"""

    def __init__(self):
        super().__init__()

        self.debug = int(getenv('DEBUG', 0))

        self.config = None

        self.parser = HtmlParser()
        self.post_process_utils = PostProcessUtils()

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

        # elasticsearch
        self.cache_info = {
            'host': None,
            'index': 'crawler-web_news-cache',
            'http_auth': None,
        }

        self.logger = Logger()

    @staticmethod
    def open_config(filename: str) -> dict:
        with open(filename, 'r') as fp:
            return dict(yaml.load(stream=fp, Loader=yaml.FullLoader))

    def update_date_range(self) -> None:
        """날짜를 갱신한다."""
        today = datetime.now(self.timezone)

        self.date_range = {
            'end': today,
            'start': today,
        }
        return

    def get_html_page(self, url_info: dict, tags: str) -> None or str:
        """웹 문서를 조회한다."""
        headers = self.headers['desktop']
        if 'headers' in url_info:
            headers.update(url_info['headers'])

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
                'level': 'ERROR',
                'message': 'html 페이지 조회 에러',
                'url_info': url_info,
                'sleep_time': sleep_time,
                'exception': str(e),
            })

            self.save_raw_html(
                url_info=url_info,
                status_code=0,
                error='html 페이지 조회 에러',
                content='',
                content_type='',
                tags=tags
            )

            sleep(sleep_time)
            return None

        # 상태 코드 확인
        status_code = resp.status_code
        if status_code // 100 != 2:
            sleep_time = 10

            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'url 조회 상태 코드 에러',
                'url_info': url_info,
                'sleep_time': sleep_time,
                'status_code': status_code,
            })

            self.save_raw_html(
                url_info=url_info,
                status_code=resp.status_code,
                error='status_code 에러',
                content='',
                content_type='',
                tags=tags,
            )

            sleep(sleep_time)
            return None

        if url_info is not None:
            if 'parser' in url_info and url_info['parser'] == 'json':
                try:
                    result = resp.json()

                    self.save_raw_html(
                        url_info=url_info,
                        status_code=resp.status_code,
                        error='',
                        content=json.dumps(result, ensure_ascii=False),
                        content_type='json',
                        tags=tags
                    )

                    return result
                except Exception as e:
                    self.logger.error(msg={
                        'level': 'ERROR',
                        'message': 'json 파싱 에러',
                        'e': str(e),
                        'resp': str(resp.content),
                    })
                    return None

        # 인코딩 변환이 지정되어 있은 경우 인코딩을 변경함
        encoding = None

        result = resp.text.strip()
        if encoding is None:
            soup, encoding = self.parser.get_encoding_type(result)

        if encoding is not None:
            result = resp.content.decode(encoding, 'ignore').strip()

        self.save_raw_html(
            url_info=url_info,
            status_code=resp.status_code,
            error='',
            content=result,
            content_type='html',
            tags=tags
        )

        return result

    def save_raw_html(self, url_info: dict, status_code: int, content: str, content_type: str, tags: str,
                      error: str = '') -> None:
        if self.cache_info['host'] is None:
            return

        try:
            ElasticSearchUtils(
                host=self.cache_info['host'],
                index=self.cache_info['index'],
                http_auth=self.cache_info['http_auth'],
                split_index=False,
            ).conn.bulk(
                index=self.cache_info['index'],
                body=[
                    {
                        'index': {
                            '_index': self.cache_info['index'],
                        }
                    },
                    {
                        'url': url_info['url'],
                        'status_code': status_code,
                        'date': datetime.now(self.timezone).isoformat(),
                        'type': content_type,
                        'content': content,
                        'error': error,
                        'tags': tags,
                        'url_info': url_info
                    }
                ],
                refresh=True,
                params={'request_timeout': 620},
            )
        except Exception as e:
            self.logger.error(msg={
                'LEVEL': 'ERROR',
                'e': str(e)
            })

        return

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

    def check_doc_id(self, doc_id: str, elastic_utils: ElasticSearchUtils, url: str, index: str, doc_history: set,
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
        is_exists = elastic_utils.conn.exists(index=index, id=doc_id)
        if is_exists is False:
            return False

        # 댓글 정보 추가 확인
        if reply_info is not None:
            field_name = reply_info['source']
            doc = elastic_utils.conn.get(
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
            'doc_url': '{host}/{index}/_doc/{id}?pretty'.format(
                id=doc_id,
                host=elastic_utils.host,
                index=elastic_utils.index,
            ),
        })

        return True
