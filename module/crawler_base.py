#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
from time import sleep

import requests
import urllib3
from werkzeug.contrib.cache import SimpleCache

from module.config import Config
from module.html_parser import HtmlParser
from module.post_process_utils import PostProcessUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class CrawlerBase(object):
    """크롤러 베이스"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_id = ''
        self.column = ''

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

    @staticmethod
    def print_message(msg):
        """화면에 메세지를 출력한다."""
        try:
            str_msg = json.dumps(msg, ensure_ascii=False, sort_keys=True)
            logging.log(level=MESSAGE, msg=str_msg)
        except Exception as e:
            logging.info(msg='{}'.format(e))

        return

    def get_html_page(self, url):
        """웹 문서를 조회한다."""
        # 페이지 조회
        try:
            resp = requests.get(url=url, headers=self.headers['desktop'],
                                allow_redirects=True, timeout=60)
        except Exception as e:
            logging.error('url 조회 에러: {} 초, {}'.format(10, e))
            sleep(10)
            return None

        # 상태 코드 확인
        status_code = resp.status_code
        if status_code // 100 != 2:
            logging.error(msg='페이지 조회 에러: {} {} {}'.format(status_code, url, resp.text))
            return None

        return resp.content

    def set_doc_history(self, doc_history):
        """문서 아이디 이력을 저장한다."""
        self.cache.set('doc_history', doc_history, timeout=600)
        return

    def get_doc_history(self):
        """문서 아이디 이력을 반환한다."""
        doc_history = self.cache.get('doc_history')

        if doc_history is None:
            doc_history = {}
            self.cache.set('doc_history', doc_history, timeout=600)

        return doc_history

    @staticmethod
    def check_doc_id(doc_id, elastic_utils, url, index, doc_history):
        """문서 아이디를 이전 기록과 비교한다."""
        # 캐쉬에 저장된 문서가 있는지 조회
        if doc_id in doc_history:
            logging.info('skip (cache) {} {}'.format(doc_id, url))
            return True

        # elasticsearch 에 문서가 있는지 조회
        is_exists = elastic_utils.elastic.exists(index=index, doc_type='doc', id=doc_id)
        if is_exists is True:
            doc_history[doc_id] = 1
            logging.info('skip (elastic) {} {}'.format(doc_id, url))
            return True

        return False

    def update_config(self):
        """설정 정보를 읽어 드린다."""
        self.cfg = Config(job_id=self.job_id)

        # request 헤더 정보
        self.headers = self.cfg.headers

        if self.column in self.cfg.parsing_info:
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
