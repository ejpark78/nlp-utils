#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from time import sleep

import requests

from module.common_utils import CommonUtils
from module.elasticsearch_utils import ElasticSearchUtils
from module.config import Config

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class AnswerList(object):
    """답변 목록을 중심으로 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_id = 'naver_kin'
        self.common_utils = CommonUtils()

        self.cfg = Config(job_id=self.job_id)

        self.headers = self.cfg.headers

    def get_partner_list(self):
        """지식 파트너 목록을 크롤링한다."""
        job_info = self.cfg.job_info['partner_list']

        elastic_utils = ElasticSearchUtils(host=job_info['host'], index=job_info['index'], bulk_size=10)

        for page in range(1, 1000):
            request_url = job_info['url_frame'].format(page=page)

            request_result = requests.get(url=request_url, headers=self.headers,
                                          allow_redirects=True, timeout=30, verify=False)

            result = request_result.json()

            if 'lists' in result:
                size = len(result['lists'])
                if size == 0:
                    break

                logging.info(msg='{}, {}'.format(size, request_url))

                for doc in result['lists']:
                    doc['_id'] = doc['u']

                    elastic_utils.save_document(index=job_info['index'], document=doc)

                elastic_utils.flush()

            sleep(5)

        return

    def get_expert_list(self):
        """분야별 전문가 목록을 크롤링한다."""
        from urllib.parse import unquote

        job_info = self.cfg.job_info['partner_list']

        elastic_utils = ElasticSearchUtils(host=job_info['host'], index=job_info['index'], bulk_size=10)

        expert_type_list = ['doctor', 'lawyer', 'labor', 'animaldoctor', 'pharmacist', 'taxacc', 'dietitian']

        for expert_type in expert_type_list:
            for page in range(1, 1000):
                request_url = job_info['url_frame'].format(expert_type=expert_type, page=page)

                request_result = requests.get(url=request_url, headers=self.headers,
                                              allow_redirects=True, timeout=30, verify=False)

                result = request_result.json()

                if 'result' in result:
                    size = len(result['result'])
                    if size == 0:
                        break

                    logging.info(msg='{}, {}'.format(size, request_url))

                    for doc in result['result']:
                        doc['expert_type'] = expert_type

                        doc['u'] = unquote(doc['encodedU'])
                        doc['_id'] = doc['u']

                        elastic_utils.save_document(index=job_info['index'], document=doc)

                    elastic_utils.flush()

                sleep(5)

        return

    def get_elite_user_list(self):
        """ 명예의 전당 채택과 년도별 사용자 목록을 가져온다. """
        job_info = self.cfg.job_info['partner_list']

        month = 0
        for year in range(2012, 2019):
            index = '{}_{}'.format(job_info['index'], year)
            elastic_utils = ElasticSearchUtils(host=job_info['host'], index=index, bulk_size=10)

            url = job_info['url_list'].format(year=year)

            result = requests.get(url=url, headers=self.headers,
                                  allow_redirects=True, timeout=30, verify=False)

            cookies = requests.utils.dict_from_cookiejar(result.cookies)
            logging.info(msg='eliteUser cookie: {} {}'.format(result, cookies))

            self.headers['referer'] = url
            for page in range(1, 6):
                list_url = job_info['url_frame'].format(year=year, month=month, page=page)

                request_result = requests.get(url=list_url, headers=self.headers, cookies=cookies,
                                              allow_redirects=True, timeout=60)

                result = request_result.json()

                if 'eliteUserList' in result:
                    logging.info(msg='{}, {}'.format(len(result['eliteUserList']), list_url))

                    for doc in result['eliteUserList']:
                        doc['_id'] = doc['u']

                        elastic_utils.save_document(index=index, document=doc)

                    elastic_utils.flush()

                sleep(5)

        return

    def get_rank_user_list(self):
        """ 분야별 전문가 목록을 추출한다. """
        job_info = self.cfg.job_info['rank_user_list']

        elastic_utils = ElasticSearchUtils(host=job_info['host'], index=job_info['index'], bulk_size=10)

        category_list = job_info['category_list']

        for dir_name in category_list:
            dir_id = category_list[dir_name]
            url = job_info['url_list'].format(dir_id=dir_id)

            result = requests.get(url=url, headers=self.headers,
                                  allow_redirects=True, timeout=30, verify=False)

            cookies = requests.utils.dict_from_cookiejar(result.cookies)
            logging.info(msg='cookie: {} {}'.format(result, cookies))

            self.headers['referer'] = url

            for u_frame in job_info['url_frame']:
                for page in range(1, 10):
                    list_url = u_frame.format(dir_id=dir_id, page=page)

                    request_result = requests.get(url=list_url, headers=self.headers, cookies=cookies,
                                                  allow_redirects=True, timeout=60)

                    result = request_result.json()

                    if 'result' in result:
                        logging.info(msg='{}, {}'.format(len(result['result']), list_url))

                        for doc in result['result']:
                            doc['_id'] = doc['u']
                            doc['rank_type'] = dir_name

                            elastic_utils.save_document(index=job_info['index'], document=doc)

                        elastic_utils.flush()

                        if len(result['result']) != 20:
                            break

                    sleep(5)

        return
