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
from urllib.parse import urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class YonhapNewsList(object):
    """연합뉴스 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_id = 'yonhapnews'
        column = 'trace_list'

        self.common_utils = CommonUtils()
        self.parser = HtmlParser()

        self.cfg = Config(job_id=self.job_id)

        # request 헤더 정보
        self.headers = self.cfg.headers

        # html 파싱 정보
        self.parsing_info = self.cfg.parsing_info[column]

        # crawler job 정보
        self.job_info = self.cfg.job_info[column]
        self.sleep = self.job_info['sleep']

        # 크롤링 상태 정보
        self.status = self.cfg.status[column]

    def daemon(self):
        """batch를 무한 반복한다."""
        while True:
            # batch 시작전 설정 변경 사항을 업데이트 한다.
            self.cfg = Config(job_id=self.job_id)
            daemon_info = self.cfg.job_info['daemon']

            # 시작
            self.batch()

            logging.info('데몬 슬립: {} 초'.format(daemon_info['sleep']))
            sleep(daemon_info['sleep'])

    def batch(self):
        """카테고리 하위 목록을 크롤링한다."""
        # 이전 카테고리를 찾는다.
        category_id = None
        if 'category' in self.status:
            category_id = self.status['category']['id']

        # 카테고리 하위 목록을 크롤링한다.
        for c in self.job_info['category']:
            if category_id is not None and c['id'] != category_id:
                continue

            category_id = None
            self.trace_list(category=c)

        return

    @staticmethod
    def get_html_page(url):
        """웹 문서를 조회한다."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/70.0.3538.110 Safari/537.36'
        }

        # 페이지 조회
        try:
            resp = requests.get(url=url, headers=headers,
                                allow_redirects=True, timeout=60)
        except Exception as e:
            logging.error('url 조회 에러: {} 초, {}'.format(10, e))
            sleep(10)
            return None

        # 상태 코드 확인
        if resp.status_code // 100 != 2:
            logging.error(msg='페이지 조회 에러: {} {} {}'.format(resp.status_code, url, resp.text))
            return None

        return resp.content

    def trace_list(self, category):
        """뉴스 목록을 크롤링한다."""
        url = self.job_info['url_frame']

        # start 부터 end 까지 반복한다.
        for page in range(self.status['start'], self.status['end'] + 1, self.status['step']):
            # 쿼리 url 생성
            query_url = url.format(page=page)

            # 기사 목록 조회
            resp = self.get_html_page(query_url)

            # 문서 저장
            self.trace_news(html=resp, base_url=query_url, category_name=category['name'])

            # 현재 크롤링 위치 저장
            self.status['start'] = page
            self.status['category'] = category

            self.cfg.save_status()

            # 현재 상태 로그 표시
            logging.info(msg='{} {:,}'.format(category['name'], page))

            sleep(self.sleep)

        # 위치 초기화
        self.status['start'] = 1
        if 'category' in self.status:
            del self.status['category']

        self.cfg.save_status()

        return

    def get_doc_id(self, url):
        """문서 아이디를 반환한다."""
        q = self.parser.parse_url(url)[2]

        return q.path.split('/')[-1]

    def trace_news(self, html, base_url, category_name):
        """개별 뉴스를 따라간다."""
        job_info = self.job_info
        elastic_utils = ElasticSearchUtils(host=job_info['host'], index=job_info['index'],
                                           bulk_size=20)

        soup = BeautifulSoup(html, 'html5lib')

        trace_tag = self.parsing_info['trace']['tag']

        trace_list = []
        self.parser.trace_tag(soup=soup, tag_list=trace_tag, index=0, result=trace_list)

        for trace in trace_list:
            # 목록에서 기사 본문 링크 추출
            item = self.parser.parse(html=None, soup=trace,
                                     parsing_info=self.parsing_info['list'])

            item['url'] = urljoin(base_url, item['url'])
            item['category'] = category_name

            doc_id = self.get_doc_id(item['url'])
            is_exists = elastic_utils.elastic.exists(index=job_info['index'], doc_type='doc', id=doc_id)
            if is_exists is True:
                logging.info('skip {} {}'.format(doc_id, item['url']))
                continue

            # 기사 본문 조회
            resp = self.get_html_page(item['url'])

            # 문서 저장
            self.save_doc(resp, item, elastic_utils=elastic_utils)

            logging.info('슬립: {} 초'.format(self.sleep))
            sleep(self.sleep)

        return False

    def save_doc(self, html, doc, elastic_utils):
        """크롤링한 문서를 저장한다."""
        soup = BeautifulSoup(html, 'html5lib')

        # html 본문에서 값 추출
        item = self.parser.parse(html=None, soup=soup,
                                 parsing_info=self.parsing_info['article'])

        doc.update(item)

        # 문서 아이디 추출
        doc['_id'] = self.get_doc_id(doc['url'])

        logging.log(level=MESSAGE, msg='문서 저장: {} {} {}'.format(doc['_id'], doc['date'], doc['title']))

        # 문서 저장
        elastic_utils.save_document(document=doc)
        elastic_utils.flush()

        return False
