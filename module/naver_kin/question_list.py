#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from time import sleep

import requests
import urllib3

from module.common_utils import CommonUtils
from module.config import Config
from module.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class QuestionList(object):
    """질문 목록 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_id = 'naver_kin'
        self.common_utils = CommonUtils()

        column = 'question_list'
        self.cfg = Config(job_id=self.job_id)

        self.headers = self.cfg.headers

        self.status = self.cfg.status[column]

        self.job_info = self.cfg.job_info[column]
        self.sleep = self.job_info['sleep']

    def batch(self):
        """ 질문 목록 전부를 가져온다. """
        category = self.job_info['category']

        for c in category:
            self.get_question_list(category=c)

        return

    def get_question_list(self, category, size=20):
        """ 네이버 지식인 경제 분야 질문 목록을 크롤링한다."""
        url = self.job_info['url_frame']

        elastic_utils = ElasticSearchUtils(host=self.job_info['host'], index=self.job_info['index'],
                                           bulk_size=50)

        # start 부터 end 까지 반복한다.
        for page in range(self.status['start'], self.status['end'], self.status['step']):
            query_url = url.format(dir_id=category['id'], size=size, page=page)

            resp = requests.get(url=query_url, headers=self.headers,
                                allow_redirects=True, timeout=60)

            result = resp.json()

            result_list = []
            if 'answerList' in result:
                result_list = result['answerList']

            if 'lists' in result:
                result_list = result['lists']

            if len(result_list) == 0:
                break

            logging.info(msg='{} {:,} ~ {:,} {:,}'.format(category['name'], page,
                                                          self.status['end'], len(result_list)))

            # 결과 저장
            for doc in result_list:
                doc['_id'] = '{}-{}-{}'.format(doc['d1Id'], doc['dirId'], doc['docId'])

                self.common_utils.print_message(msg={
                    'doc_id': doc['_id'],
                    'title': doc['title']
                })

                elastic_utils.save_document(document=doc)

            elastic_utils.flush()

            sleep(self.sleep)
        return
