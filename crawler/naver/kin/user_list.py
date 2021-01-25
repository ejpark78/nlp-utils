#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep
from urllib.parse import unquote

import requests
import urllib3

from crawler.naver.kin.base import NaverKinBase
from crawler.utils.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class UserList(NaverKinBase):
    """답변 목록을 중심으로 크롤링"""

    def __init__(self):
        super().__init__()

        self.config = None
        self.sleep_time = 10

    def batch(self, sleep_time: int, config: str) -> None:
        """ 질문 목록 전부를 가져온다. """
        self.config = self.open_config(filename=config)
        self.sleep_time = sleep_time

        self.get_rank_user_list()
        self.get_elite_user_list()
        self.get_partner_list()
        self.get_expert_list()

        return

    def get_partner_list(self) -> None:
        """지식 파트너 목록을 크롤링한다."""
        job_info = self.config['partner_list']

        elastic_utils = ElasticSearchUtils(
            host=self.config['elasticsearch']['host'],
            index=job_info['index'],
            bulk_size=10,
            http_auth=self.config['elasticsearch']['http_auth'],
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

                    self.logger.log(msg={
                        'level': 'MESSAGE',
                        'message': '지식 파트너 목록 요청',
                        'category': c,
                        'size': size,
                        'request_url': request_url,
                    })

                    for doc in result['lists']:
                        doc_id = unquote(doc['u'])

                        doc['_id'] = doc_id
                        doc['category'] = [c['name']]

                        doc_exists = elastic_utils.conn.exists(
                            index=job_info['index'],
                            id=doc_id)

                        if doc_exists is True:
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

                sleep(self.sleep_time)

        return

    def get_expert_list(self) -> None:
        """분야별 전문가 목록을 크롤링한다."""
        job_info = self.config['expert_list']

        elastic_utils = ElasticSearchUtils(
            host=self.config['elasticsearch']['host'],
            index=job_info['index'],
            bulk_size=10,
            http_auth=self.config['elasticsearch']['http_auth'],
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

                    self.logger.log(msg={
                        'level': 'MESSAGE',
                        'message': '분야별 전문가 목록 요청',
                        'expert_type': expert_type,
                        'size': size,
                        'request_url': request_url,
                    })

                    for doc in result['result']:
                        doc['expert_type'] = expert_type

                        doc['u'] = unquote(doc['encodedU'])
                        doc['_id'] = doc['u']

                        elastic_utils.save_document(index=job_info['index'], document=doc)

                    elastic_utils.flush()

                sleep(self.sleep_time)

        return

    def get_elite_user_list(self) -> None:
        """ 명예의 전당 채택과 년도별 사용자 목록을 가져온다. """
        job_info = self.config['elite_user_list']

        month = 0
        for year in range(2019, 2012, -1):
            index = '{}_{}'.format(job_info['index'], year)
            elastic_utils = ElasticSearchUtils(
                host=self.config['elasticsearch']['host'],
                index=index,
                bulk_size=10,
                http_auth=self.config['elasticsearch']['http_auth'],
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
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '명예의 전당 쿠키 정보',
                'cookies': str(cookies),
            })

            self.headers['mobile']['referer'] = url

            query = {
                'page': 1,
                'total': 20,
            }

            while query['page'] <= query['total']:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '사용자 목록 조회 조회',
                    'year': year,
                    'query': query,
                })

                list_url = job_info['url_frame'].format(year=year, month=month, page=query['page'])
                query['page'] += 1

                request_result = requests.get(
                    url=list_url,
                    headers=self.headers['mobile'],
                    cookies=cookies,
                    allow_redirects=True,
                    timeout=60,
                    verify=False
                )

                result = request_result.json()

                if 'eliteUserList' not in result:
                    break

                if len(result['eliteUserList']) == 0:
                    break

                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '명예의 전당 목록 요청',
                    'size': len(result['eliteUserList']),
                    'list_url': list_url,
                })

                for doc in result['eliteUserList']:
                    doc['_id'] = doc['u']

                    elastic_utils.save_document(index=index, document=doc)

                elastic_utils.flush()

                sleep(self.sleep_time)

        return

    def get_rank_user_list(self) -> None:
        """ 분야별 전문가 목록을 추출한다. """
        job_info = self.config['rank_user_list']

        elastic_utils = ElasticSearchUtils(
            host=self.config['elasticsearch']['host'],
            index=job_info['index'],
            bulk_size=10,
            http_auth=self.config['elasticsearch']['http_auth'],
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

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '분야별 전문가 쿠키 정보',
                'cookies': str(cookies),
            })

            self.headers['mobile']['referer'] = url

            for u_frame in job_info['url_frame']:
                query = {
                    'page': 1,
                    'total': 500,
                }

                while query['page'] <= query['total']:
                    self.logger.log(msg={
                        'level': 'MESSAGE',
                        'message': '사용자 목록 조회 조회',
                        'query': query,
                        'u_frame': u_frame,
                    })

                    list_url = u_frame.format(dir_id=c['id'], page=query['page'])
                    query['page'] += 1

                    resp = requests.get(
                        url=list_url,
                        headers=self.headers['mobile'],
                        cookies=cookies,
                        allow_redirects=True,
                        timeout=60,
                        verify=False
                    )

                    result = resp.json()

                    if 'result' not in result:
                        sleep(self.sleep_time)
                        continue

                    if 'currentTotalCount' in result:
                        try:
                            query['total'] = int(result['currentTotalCount'] / result['totalCount']) + 1
                        except Exception as e:
                            print(e)
                            break

                    self.logger.log(msg={
                        'level': 'MESSAGE',
                        'message': '랭크 전문가 목록 요청',
                        'size': len(result['result']),
                        'list_url': list_url,
                    })

                    for doc in result['result']:
                        doc_id = doc['u']

                        doc['_id'] = doc_id
                        doc['category'] = [c['name']]

                        doc_exists = elastic_utils.conn.exists(
                            index=job_info['index'],
                            id=doc_id)

                        if doc_exists is True:
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

                    sleep(self.sleep_time)

        return
