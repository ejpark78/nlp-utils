#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from time import sleep

import requests
import urllib3
from urllib.parse import unquote

from module.crawler_base import CrawlerBase
from module.utils.elasticsearch_utils import ElasticSearchUtils
from module.utils.logger import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logger = logging.getLogger()


class UserList(CrawlerBase):
    """답변 목록을 중심으로 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_category = 'naver'
        self.job_id = 'naver_kin'
        self.column = 'partner_list'

        self.update_config()

    def daemon(self):
        """batch를 무한 반복한다."""
        while True:
            # batch 시작전 설정 변경 사항을 업데이트 한다.
            self.update_config()

            daemon_info = self.cfg.job_info['daemon']

            # 시작
            self.batch()

            msg = {
                'level': 'MESSAGE',
                'message': '데몬 슬립',
                'sleep_time': daemon_info['sleep'],
            }
            logger.log(level=MESSAGE, msg=LogMsg(msg))

            sleep(daemon_info['sleep'])

    def batch(self):
        """ 질문 목록 전부를 가져온다. """
        self.get_rank_user_list()
        self.get_elite_user_list()
        self.get_partner_list()
        self.get_expert_list()

        return

    def get_partner_list(self):
        """지식 파트너 목록을 크롤링한다."""
        job_info = self.cfg.job_info['partner_list']

        elastic_utils = ElasticSearchUtils(
            host=job_info['host'],
            index=job_info['index'],
            bulk_size=10,
            http_auth=job_info['http_auth'],
        )

        category_list = job_info['category']

        for c in category_list:
            for page in range(1, 1000):
                request_url = job_info['url_frame'].format(
                    page=page,
                    dir_id=c['id'],
                )

                request_result = requests.get(
                    url=request_url,
                    headers=self.headers['mobile'],
                    allow_redirects=True,
                    timeout=30,
                    verify=False,
                )

                result = request_result.json()

                if 'lists' in result:
                    size = len(result['lists'])
                    if size == 0:
                        break

                    msg = {
                        'level': 'MESSAGE',
                        'message': '지식 파트너 목록 요청',
                        'category': c,
                        'size': size,
                        'request_url': request_url,
                    }
                    logger.log(level=MESSAGE, msg=LogMsg(msg))

                    for doc in result['lists']:
                        doc_id = unquote(doc['u'])

                        doc['_id'] = doc_id
                        doc['category'] = [c['name']]

                        if elastic_utils.elastic.exists(
                                index=job_info['index'],
                                doc_type='doc',
                                id=doc_id) is True:
                            elastic_utils.update_document(
                                index=job_info['index'],
                                field='category',
                                value=c['name'],
                                doc_id=doc_id,
                                document=doc,
                            )
                        else:
                            elastic_utils.save_document(
                                index=job_info['index'],
                                document=doc,
                            )

                    elastic_utils.flush()

                sleep(5)

        return

    def get_expert_list(self):
        """분야별 전문가 목록을 크롤링한다."""
        job_info = self.cfg.job_info['expert_list']

        elastic_utils = ElasticSearchUtils(
            host=job_info['host'],
            index=job_info['index'],
            bulk_size=10,
            http_auth=job_info['http_auth'],
        )

        expert_type_list = ['doctor', 'lawyer', 'labor', 'animaldoctor', 'pharmacist', 'taxacc', 'dietitian']

        for expert_type in expert_type_list:
            for page in range(1, 1000):
                request_url = job_info['url_frame'].format(expert_type=expert_type, page=page)

                request_result = requests.get(
                    url=request_url,
                    headers=self.headers['mobile'],
                    allow_redirects=True,
                    timeout=30,
                    verify=False,
                )

                result = request_result.json()

                if 'result' in result:
                    size = len(result['result'])
                    if size == 0:
                        break

                    msg = {
                        'level': 'MESSAGE',
                        'message': '분야별 전문가 목록 요청',
                        'expert_type': expert_type,
                        'size': size,
                        'request_url': request_url,
                    }
                    logger.log(level=MESSAGE, msg=LogMsg(msg))

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
        job_info = self.cfg.job_info['elite_user_list']

        month = 0
        for year in range(2019, 2012, -1):
            index = '{}_{}'.format(job_info['index'], year)
            elastic_utils = ElasticSearchUtils(
                host=job_info['host'],
                index=index,
                bulk_size=10,
                http_auth=job_info['http_auth'],
            )

            url = job_info['url_list'].format(year=year)

            result = requests.get(
                url=url,
                headers=self.headers['mobile'],
                allow_redirects=True,
                timeout=30,
                verify=False,
            )

            cookies = requests.utils.dict_from_cookiejar(result.cookies)
            msg = {
                'level': 'MESSAGE',
                'message': '명예의 전당 쿠키 정보',
                'cookies': str(cookies),
            }
            logger.log(level=MESSAGE, msg=LogMsg(msg))

            self.headers['mobile']['referer'] = url

            query = {
                'page': 1,
                'total': 20,
            }

            while query['page'] <= query['total']:
                msg = {
                    'level': 'MESSAGE',
                    'message': '사용자 목록 조회 조회',
                    'year': year,
                    'query': query,
                }
                logger.log(level=MESSAGE, msg=LogMsg(msg))

                list_url = job_info['url_frame'].format(year=year, month=month, page=query['page'])
                query['page'] += 1

                request_result = requests.get(
                    url=list_url,
                    headers=self.headers['mobile'],
                    cookies=cookies,
                    allow_redirects=True,
                    timeout=60,
                )

                result = request_result.json()

                if 'eliteUserList' not in result:
                    break

                if len(result['eliteUserList']) == 0:
                    break

                msg = {
                    'level': 'MESSAGE',
                    'message': '명예의 전당 목록 요청',
                    'size': len(result['eliteUserList']),
                    'list_url': list_url,
                }
                logger.log(level=MESSAGE, msg=LogMsg(msg))

                for doc in result['eliteUserList']:
                    doc['_id'] = doc['u']

                    elastic_utils.save_document(index=index, document=doc)

                elastic_utils.flush()

                sleep(5)

        return

    def get_rank_user_list(self):
        """ 분야별 전문가 목록을 추출한다. """
        job_info = self.cfg.job_info['rank_user_list']

        elastic_utils = ElasticSearchUtils(
            host=job_info['host'],
            index=job_info['index'],
            bulk_size=10,
            http_auth=job_info['http_auth'],
        )

        category_list = job_info['category']

        for c in category_list:
            url = job_info['url_list'].format(dir_id=c['id'])

            result = requests.get(
                url=url,
                headers=self.headers['mobile'],
                allow_redirects=True,
                timeout=30,
                verify=False,
            )

            # 쿠키 추출
            cookies = requests.utils.dict_from_cookiejar(result.cookies)

            msg = {
                'level': 'MESSAGE',
                'message': '분야별 전문가 쿠키 정보',
                'cookies': str(cookies),
            }
            logger.log(level=MESSAGE, msg=LogMsg(msg))

            self.headers['mobile']['referer'] = url

            for u_frame in job_info['url_frame']:
                query = {
                    'page': 1,
                    'total': 500,
                }

                while query['page'] <= query['total']:
                    msg = {
                        'level': 'MESSAGE',
                        'message': '사용자 목록 조회 조회',
                        'query': query,
                        'u_frame': u_frame,
                    }
                    logger.log(level=MESSAGE, msg=LogMsg(msg))

                    list_url = u_frame.format(dir_id=c['id'], page=query['page'])
                    query['page'] += 1

                    resp = requests.get(
                        url=list_url,
                        headers=self.headers['mobile'],
                        cookies=cookies,
                        allow_redirects=True,
                        timeout=60,
                    )

                    result = resp.json()

                    if 'result' not in result:
                        sleep(5)
                        continue

                    if 'currentTotalCount' in result:
                        try:
                            query['total'] = int(result['currentTotalCount'] / result['totalCount']) + 1
                        except Exception as e:
                            print(e)
                            break

                    msg = {
                        'level': 'MESSAGE',
                        'message': '랭크 전문가 목록 요청',
                        'size': len(result['result']),
                        'list_url': list_url,
                    }
                    logger.log(level=MESSAGE, msg=LogMsg(msg))

                    for doc in result['result']:
                        doc_id = doc['u']

                        doc['_id'] = doc_id
                        doc['category'] = [c['name']]

                        if elastic_utils.elastic.exists(
                                index=job_info['index'],
                                doc_type='doc',
                                id=doc_id) is True:
                            elastic_utils.update_document(
                                index=job_info['index'],
                                field='category',
                                value=c['name'],
                                doc_id=doc_id,
                                document=doc,
                            )
                        else:
                            elastic_utils.save_document(
                                index=job_info['index'],
                                document=doc,
                            )

                    elastic_utils.flush()

                    if len(result['result']) != 20:
                        break

                    sleep(5)

        return
