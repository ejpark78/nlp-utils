#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import re
from datetime import datetime
from urllib.parse import urljoin

import urllib3
from bs4 import BeautifulSoup
from time import sleep

from module.crawler_base import CrawlerBase
from module.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class WebNewsCrawler(CrawlerBase):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self, job_id='', column=''):
        """ 생성자 """
        super().__init__()

        self.job_id = job_id
        self.column = column

    def daemon(self):
        """데몬으로 실행"""
        while True:
            # batch 시작전 설정 변경 사항을 업데이트 한다.
            self.update_config()
            daemon_info = self.cfg.job_info['daemon']

            # 시작
            self.batch()

            logging.info('데몬 슬립: {} 초'.format(daemon_info['sleep']))
            sleep(daemon_info['sleep'])

    def batch(self):
        """카테고리 하위 목록을 크롤링한다."""
        # 카테고리 하위 목록을 크롤링한다.
        for job in self.job_info:
            self.sleep_time = job['sleep']

            self.trace_list(job=job)

        return

    def trace_list(self, job):
        """뉴스 목록을 크롤링한다."""
        url = job['url_frame']

        # start 부터 end 까지 반복한다.
        for page in range(self.status['start'], self.status['end'] + 1, self.status['step']):
            # 쿼리 url 생성
            query_url = url.format(page=page)

            # 기사 목록 조회
            resp = self.get_html_page(query_url)
            if resp is None:
                continue

            # 문서 저장
            early_stop = self.trace_news(html=resp, base_url=query_url, job=job)
            if early_stop is True:
                break

            # 현재 크롤링 위치 저장
            self.status['start'] = page

            self.cfg.save_status()

            # 현재 상태 로그 표시
            msg = '기사 목록 조회, 슬립: {} 초, {} {:,}'.format(self.sleep_time, job['category'], page)
            logging.info(msg=msg)
            sleep(self.sleep_time)

        # 위치 초기화
        self.status['start'] = 1
        if 'category' in self.status:
            del self.status['category']

        self.cfg.save_status()

        return

    def get_doc_id(self, url, job):
        """문서 아이디를 반환한다."""
        id_frame = job['id_frame']

        q, _, url_info = self.parser.parse_url(url)

        result = '{}.{}'.format(url_info.path, '.'.join(q.values()))

        if id_frame['type'] == 'path':
            result = url_info.path

            for pattern in id_frame['replace']:
                result = re.sub(pattern['from'], pattern['to'], result, flags=re.DOTALL)
        elif id_frame['type'] == 'query':
            if len(q) == 0:
                logging.info('skip {}'.format(url))
                return None

            result = id_frame['frame'].format(**q)

        result = result.strip()

        return result

    def parse_html(self, html):
        """html 문서를 파싱한다."""
        if self.parsing_info['parser'] == 'lxml':
            soup = BeautifulSoup(html, 'lxml')
        else:
            soup = BeautifulSoup(html, 'html5lib')

        return soup

    def trace_news(self, html, base_url, job):
        """개별 뉴스를 따라간다."""
        elastic_utils = ElasticSearchUtils(host=job['host'], index=job['index'], bulk_size=20)

        soup = self.parse_html(html=html)

        trace_tag = self.parsing_info['trace']['tag']

        trace_list = []
        self.parser.trace_tag(soup=soup, tag_list=trace_tag, index=0, result=trace_list)

        # 기사 목록이 3개 이하인 경우 조기 종료
        if len(trace_list) < 3:
            logging.info('early stopping : size {}'.format(len(trace_list)))
            return True

        # url 저장 이력 조회
        doc_history = self.get_doc_history()

        _, base_url, _ = self.parser.parse_url(base_url)

        # 개별 뉴스를 따라간다.
        for trace in trace_list:
            # 목록에서 기사 본문 링크 추출
            item = self.parser.parse(html=None, soup=trace,
                                     parsing_info=self.parsing_info['list'])

            if isinstance(item['url'], list) and len(item['url']) > 0:
                item['url'] = item['url'][0]

            item['url'] = urljoin(base_url, item['url'])
            item['category'] = job['category']

            doc_id = self.get_doc_id(url=item['url'], job=job)
            if doc_id is None:
                continue

            is_skip = self.check_doc_id(doc_id=doc_id, elastic_utils=elastic_utils,
                                        url=item['url'], index=job['index'], doc_history=doc_history)
            if is_skip is True:
                continue

            # 기사 본문 조회
            resp = self.get_html_page(item['url'])
            if resp is None:
                continue

            # 문서 저장
            item['_id'] = doc_id
            doc = self.save_doc(resp, item, elastic_utils=elastic_utils)

            doc_history[doc_id] = 1

            # 후처리 작업 실행
            if 'post_process' not in job:
                job['post_process'] = None

            self.post_process_utils.insert_job(document=doc, post_process_list=job['post_process'])

            logging.info('슬립: {} 초'.format(self.sleep_time))
            sleep(self.sleep_time)

        # 캐쉬 저장
        self.set_doc_history(doc_history)

        return False

    def save_doc(self, html, doc, elastic_utils):
        """크롤링한 문서를 저장한다."""
        soup = self.parse_html(html=html)

        # html 본문에서 값 추출
        item = self.parser.parse(soup=soup, parsing_info=self.parsing_info['article'])

        doc.update(item)

        # 문서 아이디 추출
        doc['curl_date'] = datetime.now()

        msg = '문서 저장: {} {} {}'.format(doc['_id'], doc['date'], doc['title'])
        logging.log(level=MESSAGE, msg=msg)

        # 문서 저장
        elastic_utils.save_document(document=doc)
        elastic_utils.flush()

        return doc
