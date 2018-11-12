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
from module.elasticsearch_utils import ElasticSearchUtils
from module.naver_kin.config import Config

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

        self.common_utils = CommonUtils()

        cfg = Config()

        self.headers = cfg.headers
        self.job_info = cfg.job_info['question_list']

    def batch(self):
        """ 질문 목록 전부를 가져온다. """
        dir_id_list = [4, 11, 1, 2, 3, 8, 7, 6, 9, 10, 5, 13, 12, 20]
        for dir_id in dir_id_list:
            self.get_question_list(url=self.job_info['url_frame'],
                                   host=self.job_info['host'],
                                   index=self.job_info['index'],
                                   dir_id=dir_id, end=500)

        return

    def get_question_list(self, url, host, index, dir_id=4, start=1, end=90000, size=20):
        """ 네이버 지식인 경제 분야 질문 목록을 크롤링한다."""
        delay = 5

        elastic_utils = ElasticSearchUtils(host=host, index=index, bulk_size=10)

        for page in range(start, end):
            query_url = url.format(dir_id=dir_id, size=size, page=page)

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

            logging.info(msg='{} {:,} ~ {:,} {:,}'.format(dir_id, page, end, len(result_list)))

            # 결과 저장
            for doc in result_list:
                doc['_id'] = '{}-{}-{}'.format(doc['d1Id'], doc['dirId'], doc['docId'])

                self.common_utils.print_message(msg={
                    'doc_id': doc['_id'],
                    'title': doc['title']
                })

                elastic_utils.save_document(document=doc)

            elastic_utils.flush()

            sleep(delay)
        return
