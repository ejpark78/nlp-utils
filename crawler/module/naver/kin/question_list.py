#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep

import requests
import urllib3

from module.web_news.base import WebNewsBase
from utils.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class QuestionList(WebNewsBase):
    """질문 목록 크롤링"""

    def __init__(self, sleep_time):
        """ 생성자 """
        super().__init__()

        self.job_category = 'naver'
        self.job_id = 'naver_kin'
        self.column = 'question_list'

        self.sleep_time = sleep_time

    def daemon(self, column):
        """batch를 무한 반복한다."""
        while True:
            # batch 시작전 설정 변경 사항을 업데이트 한다.
            self.update_config(filename=None, job_id=self.job_id, job_category=self.job_category, column=self.env.column)

            daemon_info = self.cfg.job_info['daemon']

            # 시작
            self.batch(column=column)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '데몬 슬립',
                'sleep_time': daemon_info['sleep'],
            })

            sleep(daemon_info['sleep'])

    def batch(self, column):
        """ 질문 목록 전부를 가져온다. """
        self.update_config(filename=None, job_id=self.job_id, job_category=self.job_category, column=self.env.column)

        for c in self.job_info['category']:
            # 답변 목록
            if column == 'answer':
                self.column = 'answer_list'
                self.update_config(filename=None, job_id=self.job_id, job_category=self.job_category, column=self.env.column)

                self.get_answer_list(category=c)
            else:
                # 질문 목록
                self.column = 'question_list'
                self.update_config(filename=None, job_id=self.job_id, job_category=self.job_category, column=self.env.column)

                self.get_question_list(category=c)

        return

    def get_answer_list(self, category):
        """ 사용자별 답변 목록를 가져온다. """
        from urllib.parse import unquote
        # https://m.kin.naver.com/mobile/user/answerList.nhn?page=3&countPerPage=20&dirId=0&u=LOLmw2nTPw02cmSW5fzHYaVycqNwxX3QNy3VuztCb6c%3D

        elastic_utils = ElasticSearchUtils(
            host=self.job_info['host'],
            index=self.job_info['index'],
            bulk_size=10,
            http_auth=self.job_info['http_auth'],
        )

        query = {
            '_source': ['u', 'name', 'companyName', 'partnerName', 'viewUserId', 'encodedU'],
            'query': {
                'match': {
                    'category': '고민Q&A'
                }
            }
        }

        user_list = elastic_utils.dump(
            index='crawler-naver-kin-rank_user_list,crawler-naver-kin-partner_list',
            query=query,
        )

        for doc in user_list:
            query = {
                'page': 1,
                'total': 500,
            }

            while query['page'] <= query['total']:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '질문 조회',
                    'query': query,
                })

                if 'encodedU' in doc:
                    query_url = self.job_info['url_frame'].format(
                        page=query['page'],
                        user_id=doc['encodedU'],
                    )
                else:
                    query_url = self.job_info['url_frame'].format(
                        page=query['page'],
                        user_id=unquote(doc['u']),
                    )

                is_stop, query['total'] = self.get_page(url=query_url, elastic_utils=elastic_utils)
                if is_stop is True:
                    break

                sleep(self.sleep_time)

        return

    def get_question_list(self, category, size=20):
        """ 네이버 지식인 경제 분야 질문 목록을 크롤링한다."""
        elastic_utils = ElasticSearchUtils(
            host=self.job_info['host'],
            index=self.job_info['index'],
            bulk_size=50,
            http_auth=self.job_info['http_auth'],
        )

        query = {
            'page': 1,
            'total': 500,
        }

        while query['page'] <= query['total']:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '질문 조회',
                'query': query,
            })

            query_url = self.job_info['url_frame'].format(
                size=size,
                page=query['page'],
                dir_id=category['id'],
            )

            is_stop, query['total'] = self.get_page(url=query_url, elastic_utils=elastic_utils)
            if is_stop is True:
                break

            query['page'] += 1

            sleep(self.sleep_time)

        return

    def get_page(self, url, elastic_utils):
        """한 페이지를 가져온다."""
        total_page = -1

        try:
            resp = requests.get(
                url=url,
                headers=self.headers['mobile'],
                allow_redirects=True,
                timeout=60,
                verify=False
            )
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '질문 목록 조회 에러',
                'query_url': url,
                'exception': str(e),
            })

            sleep(self.sleep_time)
            return True, total_page

        resp_info = None
        try:
            resp_info = resp.json()

            is_stop = self.save_doc(
                url=url,
                result=resp_info,
                elastic_utils=elastic_utils,
            )

            if 'countPerPage' in resp_info:
                if 'totalCount' in resp_info:
                    total_page = int(resp_info['totalCount'] / resp_info['countPerPage']) + 1

                if 'answerCount' in resp_info:
                    total_page = int(resp_info['answerCount'] / resp_info['countPerPage']) + 1

            if is_stop is True:
                return True, total_page
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '질문 목록 저장 에러',
                'query_url': url,
                'resp_info': resp_info,
                'exception': str(e),
            })

        return False, total_page

    def save_doc(self, url, result, elastic_utils):
        """크롤링 결과를 저장한다."""
        from urllib.parse import urljoin

        result_list = []
        if 'answerList' in result:
            result_list = result['answerList']

        if 'lists' in result:
            result_list = result['lists']

        if len(result_list) == 0:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '빈 문서 목록 반환',
                'url': url,
                'result': result,
            })
            return True

        # 결과 저장
        for doc in result_list:
            if 'd1Id' in doc:
                doc_id = '{d1}-{dir}-{doc}'.format(
                    d1=doc['d1Id'],
                    dir=doc['dirId'],
                    doc=doc['docId'],
                )
            else:
                doc_id = '{dir}-{doc}'.format(
                    dir=doc['dirId'],
                    doc=doc['docId'],
                )

            if 'detailUrl' in doc:
                doc['detailUrl'] = urljoin(url, doc['detailUrl'])

            doc['_id'] = doc_id

            elastic_utils.save_document(document=doc)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '문서 저장 성공',
                'doc_url': '{host}/{index}/_doc/{id}?pretty'.format(
                    host=elastic_utils.host,
                    index=elastic_utils.index,
                    id=doc_id,
                )
            })

        elastic_utils.flush()

        return False
