#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from time import sleep

import requests
import urllib3
from bs4 import BeautifulSoup

from module.common_utils import CommonUtils
from module.config import Config
from module.elasticsearch_utils import ElasticSearchUtils
from module.html_parser import HtmlParser

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class TermList(object):
    """백과사전 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_id = 'naver_terms'

        self.common_utils = CommonUtils()
        self.parser = HtmlParser()

        self.cfg = Config(job_id=self.job_id)

        self.headers = self.cfg.headers

        # html 파싱 정보
        self.parsing_info = self.cfg.parsing_info['term_list']

        # crawler job 정보
        self.job_info = self.cfg.job_info['term_list']
        self.category = self.job_info['category']
        self.sleep = self.job_info['sleep']

        # 크롤링 상태 정보
        self.status = self.cfg.status

    def batch(self):
        """카테고리 하위 목록을 크롤링한다."""
        # 이전 카테고리를 찾는다.
        category_id = None
        if 'category_id' in self.status:
            category_id = self.status['category_id']

        # 카테고리 하위 목록을 크롤링한다.
        for c in self.category:
            if category_id is not None and c['category_id'] != category_id:
                continue

            category_id = None
            self.get_term_list(category_id=c['category_id'], category_name=c['name'])

        return

    def get_term_list(self, category_id, category_name):
        """용어 목록을 크롤링한다."""
        history = {}
        count = {
            'prev': -1
        }

        url = self.job_info['url_frame']
        trace_tag = self.parsing_info['trace']['tag']

        # start 부터 end 까지 반복한다.
        for page in range(self.status['start'], self.status['end'], self.status['step']):
            # 쿼리 url 생성
            query_url = url.format(category_id=category_id, page=page)

            # 페이지 조회
            resp = requests.get(url=query_url, headers=self.headers,
                                allow_redirects=True, timeout=60)

            # 문서 저장
            is_stop = self.save_doc(html=resp.content, trace_tag=trace_tag, count=count,
                                    category_name=category_name, history=history)

            # 현재 크롤링 위치 저장
            self.status['start'] = page
            self.status['category_id'] = category_id
            self.status['category_name'] = category_name

            self.cfg.save_status()

            # 현재 상태 로그 표시
            logging.info(msg='{} {:,}, {:,} {:,}'.format(category_id, page, count['prev'], count['element']))

            if is_stop is True:
                break

            sleep(self.sleep)

        # 위치 초기화
        self.status['start'] = 1
        del self.status['category_id']

        return

    def save_doc(self, html, trace_tag, history, category_name, count):
        """크롤링한 문서를 저장한다."""
        elastic_utils = ElasticSearchUtils(host=self.job_info['host'], index=self.job_info['index'],
                                           bulk_size=20)

        soup = BeautifulSoup(html, 'html5lib')

        count['element'] = 0
        count['overlap'] = -1

        for trace in trace_tag:
            item_list = soup.find_all(trace['name'], trace['attribute'])
            for item in item_list:
                # html 본문에서 값 추출
                doc = self.parser.parse(html=None, soup=item,
                                        parsing_info=self.parsing_info['values'])

                # url 파싱
                q, _, _ = self.parser.parse_url(doc['detail_link'])

                # 문서 메타정보 등록
                doc['_id'] = '{}-{}'.format(q['cid'], q['docId'])

                doc['cid'] = q['cid']
                doc['doc_id'] = q['docId']
                doc['category'] = category_name

                # 저장 로그 표시
                msg = '{} {} {} {}'.format(category_name, doc['_id'], doc['name'], doc['define'][:30])
                logging.info(msg=msg)

                if doc['_id'] in history:
                    count['overlap'] += 1

                history[doc['_id']] = 1

                count['element'] += 1
                elastic_utils.save_document(document=doc)

            elastic_utils.flush()

        if count['overlap'] == count['element']:
            return True

        # 종료 조건
        if count['prev'] > 0 and count['prev'] > count['element']:
            return True

        count['prev'] = count['element']

        return False
