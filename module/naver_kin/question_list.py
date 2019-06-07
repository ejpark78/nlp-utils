#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from time import sleep

import requests
import urllib3

from module.crawler_base import CrawlerBase
from module.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

logger = logging.getLogger()


class QuestionList(CrawlerBase):
    """질문 목록 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_category = 'naver'
        self.job_id = 'naver_kin'
        self.column = 'question_list'

    def daemon(self):
        """batch를 무한 반복한다."""
        while True:
            # batch 시작전 설정 변경 사항을 업데이트 한다.
            self.update_config()

            daemon_info = self.cfg.job_info['daemon']

            # 시작
            self.batch()

            logger.info('데몬 슬립: {} 초'.format(daemon_info['sleep']))
            sleep(daemon_info['sleep'])

    def batch(self):
        """ 질문 목록 전부를 가져온다. """
        self.update_config()

        category_id = None
        if 'category' in self.status:
            category_id = self.status['category']['id']

        for c in self.job_info['category']:
            if category_id is not None and c['id'] != category_id:
                continue

            category_id = None
            self.get_question_list(category=c)

        return

    def get_question_list(self, category, size=20):
        """ 네이버 지식인 경제 분야 질문 목록을 크롤링한다."""
        elastic_utils = ElasticSearchUtils(
            host=self.job_info['host'],
            index=self.job_info['index'],
            bulk_size=50,
            http_auth=self.job_info['http_auth'],
        )

        # start 부터 end 까지 반복한다.
        for page in range(self.status['start'], self.status['end'], self.status['step']):
            query_url = self.job_info['url_frame'].format(dir_id=category['id'], size=size, page=page)

            try:
                resp = requests.get(url=query_url, headers=self.headers['mobile'],
                                    allow_redirects=True, timeout=60)
            except Exception as e:
                logger.error(msg='{}'.format(e))
                sleep(10)
                continue

            try:
                is_stop = self.save_doc(result=resp.json(), elastic_utils=elastic_utils)
                if is_stop is True:
                    break
            except Exception as e:
                logger.error(msg='{}'.format(e))
                break

            # 현재 상태 저장
            self.status['start'] = page
            self.status['category'] = category

            self.cfg.save_status()

            # 로그 표시
            logger.info(msg='{} {:,} ~ {:,}'.format(category['name'], page, self.status['end']))

            sleep(self.sleep_time)

        # status 초기화
        self.status['start'] = 1
        if 'category' in self.status:
            del self.status['category']

        self.cfg.save_status()

        return

    @staticmethod
    def save_doc(result, elastic_utils):
        """크롤링 결과를 저장한다."""
        result_list = []
        if 'answerList' in result:
            result_list = result['answerList']

        if 'lists' in result:
            result_list = result['lists']

        if len(result_list) == 0:
            return True

        # 결과 저장
        for doc in result_list:
            doc_id = '{}-{}-{}'.format(doc['d1Id'], doc['dirId'], doc['docId'])
            doc['_id'] = doc_id

            elastic_utils.save_document(document=doc)
            logger.info(msg='{} {}'.format(doc_id, doc['title']))

        elastic_utils.flush()

        return False
