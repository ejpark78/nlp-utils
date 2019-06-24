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
from module.logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logger = logging.getLogger()


class QuestionList(CrawlerBase):
    """질문 목록 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_category = 'naver'
        self.job_id = 'naver_kin'
        self.column = 'question_list'

    def daemon(self, column):
        """batch를 무한 반복한다."""
        while True:
            # batch 시작전 설정 변경 사항을 업데이트 한다.
            self.update_config()

            daemon_info = self.cfg.job_info['daemon']

            # 시작
            self.batch(column=column)

            msg = {
                'level': 'MESSAGE',
                'message': '데몬 슬립',
                'sleep_time': daemon_info['sleep'],
            }
            logger.log(level=MESSAGE, msg=LogMsg(msg))

            sleep(daemon_info['sleep'])

    def batch(self, column):
        """ 질문 목록 전부를 가져온다. """
        self.update_config()

        category_id = None
        if 'category' in self.status:
            category_id = self.status['category']['id']

        for c in self.job_info['category']:
            if category_id is not None and c['id'] != category_id:
                continue

            category_id = None

            # 답변 목록
            if column == 'answer':
                self.column = 'answer_list'
                self.update_config()

                self.get_answer_list(category=c)
            else:
                # 질문 목록
                self.column = 'question_list'
                self.update_config()

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

        # crawler-naver-kin-rank_user_list
        # crawler-naver-kin-partner_list
        user_list = elastic_utils.dump(
            index='crawler-naver-kin-rank_user_list,crawler-naver-kin-partner_list',
            query=query,
        )

        for doc in user_list:
            for page in range(self.status['start'], self.status['end'], self.status['step']):
                if 'encodedU' in doc:
                    query_url = self.job_info['url_frame'].format(
                        page=page,
                        user_id=doc['encodedU'],
                    )
                else:
                    query_url = self.job_info['url_frame'].format(
                        page=page,
                        user_id=unquote(doc['u']),
                    )

                is_stop = self.get_page(url=query_url, elastic_utils=elastic_utils)
                if is_stop is True:
                    break

                self.update_state(page=page, category=category)

            # status 초기화
            self.status['start'] = 1
            if 'category' in self.status:
                del self.status['category']

            self.cfg.save_status()

        return

    def get_question_list(self, category, size=20):
        """ 네이버 지식인 경제 분야 질문 목록을 크롤링한다."""
        elastic_utils = ElasticSearchUtils(
            host=self.job_info['host'],
            index=self.job_info['index'],
            bulk_size=50,
            http_auth=self.job_info['http_auth'],
        )

        # status 초기화
        self.status['start'] = 1

        # start 부터 end 까지 반복한다.
        for page in range(self.status['start'], self.status['end'], self.status['step']):
            query_url = self.job_info['url_frame'].format(
                size=size,
                page=page,
                dir_id=category['id'],
            )

            is_stop = self.get_page(url=query_url, elastic_utils=elastic_utils)
            if is_stop is True:
                break

            self.update_state(page=page, category=category)

        # status 초기화
        self.status['start'] = 1
        if 'category' in self.status:
            del self.status['category']

        self.cfg.save_status()

        return

    def get_page(self, url, elastic_utils):
        """한 페이지를 가져온다."""
        try:
            resp = requests.get(
                url=url,
                headers=self.headers['mobile'],
                allow_redirects=True,
                timeout=60,
            )
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '질문 목록 조회 에러',
                'query_url': url,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

            sleep(10)
            return True

        try:
            is_stop = self.save_doc(
                url=url,
                result=resp.json(),
                elastic_utils=elastic_utils,
            )
            if is_stop is True:
                return True
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '질문 목록 저장 에러',
                'query_url': url,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        return False

    def update_state(self, page, category):
        """현재 상태를 갱신한다."""
        self.status['start'] = page
        self.status['category'] = category

        self.cfg.save_status()

        # 로그 표시
        msg = {
            'level': 'INFO',
            'message': '기사 저장 성공',
            'category_name': category['name'],
            'page': page,
            'end': self.status['end'],
        }
        logger.info(msg=LogMsg(msg))

        sleep(self.sleep_time)
        return

    @staticmethod
    def save_doc(url, result, elastic_utils):
        """크롤링 결과를 저장한다."""
        from urllib.parse import urljoin

        result_list = []
        if 'answerList' in result:
            result_list = result['answerList']

        if 'lists' in result:
            result_list = result['lists']

        if len(result_list) == 0:
            msg = {
                'level': 'ERROR',
                'message': '빈 문서 목록 반환',
                'url': url,
                'result': result,
            }
            logger.error(msg=LogMsg(msg))
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

            msg = {
                'level': 'MESSAGE',
                'message': '문서 저장 성공',
                'doc_url': '{host}/{index}/doc/{id}?pretty'.format(
                    host=elastic_utils.host,
                    index=elastic_utils.index,
                    id=doc_id,
                )
            }
            logger.log(level=MESSAGE, msg=LogMsg(msg))

        elastic_utils.flush()

        return False
