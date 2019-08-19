#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import re
from datetime import datetime
from time import sleep

import pytz
import requests
import urllib3
from dateutil.relativedelta import relativedelta
from werkzeug.contrib.cache import SimpleCache

from module.config import Config
from module.html_parser import HtmlParser
from module.logging_format import LogMessage as LogMsg
from module.post_process_utils import PostProcessUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

logger = logging.getLogger()


class CrawlerBase(object):
    """크롤러 베이스"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_category = ''
        self.job_id = ''
        self.column = ''

        self.config = None

        self.parser = HtmlParser()
        self.post_process_utils = PostProcessUtils()

        self.cfg = None
        self.headers = None

        self.parsing_info = None

        # crawler job 정보
        self.job_info = None
        self.sleep_time = 2

        # 크롤링 상태 정보
        self.status = None

        # 후처리 정보
        self.post_process_list = None
        self.cache = SimpleCache()

        # 로컬 시간 정보
        self.timezone = pytz.timezone('Asia/Seoul')

        # 날짜 범위
        self.date_range = None

    def update_date_range(self):
        """날짜를 갱신한다."""
        today = datetime.now(self.timezone)

        self.date_range = {
            'end': today,
            'start': today + relativedelta(weeks=-1),
        }
        return

    @staticmethod
    def get_encoding_type(html_body):
        """ 메타 정보에서 인코딩 정보 반환한다."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_body, 'html5lib')

        if soup.meta is None:
            return soup, None

        encoding = soup.meta.get('charset', None)
        if encoding is None:
            encoding = soup.meta.get('content-type', None)

            if encoding is None:
                content = soup.meta.get('content', None)

                if content is None:
                    content = html_body

                match = re.search('charset=(.*)', content)
                if match:
                    encoding = match.group(1)
                else:
                    return soup, None

        return soup, encoding

    def get_html_page(self, url_info):
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

            msg = {
                'level': 'ERROR',
                'message': 'html 페이지 조회 에러',
                'url_info': url_info,
                'sleep_time': sleep_time,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

            sleep(sleep_time)
            return None

        # 상태 코드 확인
        status_code = resp.status_code
        if status_code // 100 != 2:
            sleep_time = 10

            msg = {
                'level': 'ERROR',
                'message': 'url 조회 상태 코드 에러',
                'url_info': url_info,
                'sleep_time': sleep_time,
                'status_code': status_code,
            }
            logger.error(msg=LogMsg(msg))

            sleep(sleep_time)
            return None

        if url_info is not None:
            if 'parser' in url_info and url_info['parser'] == 'json':
                return resp.json()

        # 인코딩 변환이 지정되어 있은 경우 인코딩을 변경함
        encoding = None

        result = resp.text
        if encoding is None:
            soup, encoding = self.get_encoding_type(result)

        if encoding is not None:
            result = resp.content.decode(encoding, 'ignore')

        return result

    def set_history(self, value, name):
        """문서 아이디 이력을 저장한다."""
        self.cache.set(name, value, timeout=600)
        return

    def get_history(self, name, default):
        """문서 아이디 이력을 반환한다."""
        value = self.cache.get(name)

        if value is None:
            value = default
            self.cache.set(name, value, timeout=600)

        return value

    def get_dict_value(self, data, key_list, result):
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
    def check_doc_id(doc_id, elastic_utils, url, index, doc_history):
        """문서 아이디를 이전 기록과 비교한다."""
        # 캐쉬에 저장된 문서가 있는지 조회
        if doc_id in doc_history:
            msg = {
                'level': 'INFO',
                'message': '중복 문서, 건너뜀',
                'doc_id': doc_id,
                'url': url,
            }
            logger.info(msg=LogMsg(msg))
            return True

        # 문서가 있는지 조회
        is_exists = elastic_utils.elastic.exists(index=index, doc_type='doc', id=doc_id)
        if is_exists is True:
            doc_history[doc_id] = 1

            msg = {
                'level': 'INFO',
                'message': 'elasticsearch 에 존재함, 건너뜀',
                'doc_id': doc_id,
                'url': url,
            }
            logger.info(msg=LogMsg(msg))
            return True

        return False

    def update_config(self):
        """설정 정보를 읽어 드린다."""
        self.cfg = Config(
            config=self.config,
            job_id=self.job_id,
            job_category=self.job_category,
        )

        # request 헤더 정보
        self.headers = self.cfg.headers

        if self.cfg.parsing_info is not None and self.column in self.cfg.parsing_info:
            self.parsing_info = self.cfg.parsing_info[self.column]

        # crawler job 정보
        if self.column in self.cfg.job_info:
            self.job_info = self.cfg.job_info[self.column]

            if 'sleep' in self.job_info:
                self.sleep_time = self.job_info['sleep']

        # 크롤링 상태 정보
        if self.column in self.cfg.status:
            self.status = self.cfg.status[self.column]

        # 후처리 정보
        if 'post_process' in self.job_info:
            self.post_process_list = self.job_info['post_process']

        return
