#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from time import sleep

import requests
import urllib3
from bs4 import BeautifulSoup
from requests import Response

from crawler.naver.kin.base import NaverKinBase
from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.utils.html_parser import HtmlParser

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class QuestionDetail(NaverKinBase):
    """질문 상세 페이지 크롤링"""

    def __init__(self):
        super().__init__()

        self.job_info = {}
        self.sleep_time = 10

        self.parser = HtmlParser()

    def batch(self, sleep_time: float, column: str, match_phrase: str, config: str) -> None:
        """상세 페이지를 크롤링한다."""
        self.config = self.open_config(filename=config)
        self.job_info = self.config['detail']
        self.sleep_time = sleep_time

        self.job_info['index'] = 'crawler-naver-kin-answer_list'
        if column == 'question':
            self.job_info['index'] = 'crawler-naver-kin-question_list'

        elastic_utils = ElasticSearchUtils(
            host=self.config['elasticsearch']['host'],
            index=self.job_info['index'],
            bulk_size=10,
            http_auth=self.config['elasticsearch']['http_auth'],
        )

        # 질문 목록 조회
        doc_list = self.get_doc_list(
            index=self.job_info['index'],
            elastic_utils=elastic_utils,
            match_phrase=match_phrase,
        )

        i = -1
        size = len(doc_list)

        for doc in doc_list:
            # 문서 아이디 생성
            if 'd1Id' not in doc:
                doc['d1Id'] = str(doc['dirId'])[0]

            i += 1
            doc_id = '{d1Id}-{dirId}-{docId}'.format(**doc)

            # 이미 받은 항목인지 검사
            if self.job_info['index'].find('question_list') > 0 or self.job_info['index'].find('answer_list') > 0:
                is_skip = elastic_utils.exists(
                    index=self.job_info['index'],
                    list_index=self.job_info['index'],
                    doc_id=doc_id,
                    list_id=doc['_id'],
                )

                if is_skip is True:
                    self.logger.info(msg={
                        'level': 'INFO',
                        'message': 'SKIP',
                        'doc_id': doc_id,
                        'index': self.job_info['index'],
                    })
                    continue

            # 질문 상세 페이지 크롤링
            request_url = self.job_info['url_frame'].format(**doc)

            resp = requests.get(
                url=request_url,
                headers=self.headers['mobile'],
                allow_redirects=True,
                timeout=60,
                verify=False
            )

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '상세 질문',
                'i': i,
                'size': size,
                'doc_id': doc_id,
                'request_url': request_url,
            })

            # 저장
            self.save_doc(
                resp=resp,
                index=self.job_info['index'],
                doc_id=doc_id,
                list_id=doc['_id'],
                base_url=request_url,
                elastic_utils=elastic_utils,
            )

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '슬립',
                'sleep_time': self.sleep_time,
            })

            sleep(self.sleep_time)

        return

    def save_doc(self, resp: Response, elastic_utils: ElasticSearchUtils, index: str, doc_id: str, list_id: str,
                 base_url: str) -> None:
        """크롤링 문서를 저장한다."""
        soup, encoding = self.parser.get_encoding_type(html_body=resp.text)

        html = resp.text
        if encoding is not None:
            html = resp.content.decode(encoding, 'ignore')

        soup = BeautifulSoup(html, 'html5lib')

        # 이미 삭제된 질문일 경우
        if soup is not None:
            # 질문 정보 추출
            doc = self.parser.parse(
                html=None,
                soup=soup,
                parsing_info=self.config['detail']['parsing'],
                base_url=base_url
            )

            if 'question' not in doc:
                # 비공계 처리된 경우
                elastic_utils.move_document(
                    source_id=list_id,
                    document_id=doc_id,
                    source_index=index,
                    target_index='{}_done'.format(index),
                )
                return

            doc['_id'] = doc_id

            # 문서 저장
            elastic_utils.save_document(
                index=self.job_info['index'],
                document=doc,
            )
            elastic_utils.flush()

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '상세 답변 저장 성공',
                'question': doc['question'],
                'doc_url': elastic_utils.get_doc_url(document_id=doc_id)
            })

        # 질문 목록에서 완료 목록으로 이동
        elastic_utils.move_document(
            source_id=list_id,
            document_id=doc_id,
            source_index=index,
            target_index='{}_done'.format(index),
        )

        return

    @staticmethod
    def get_doc_list(elastic_utils: ElasticSearchUtils, index: str, match_phrase: str) -> list:
        """질문 목록을 조회한다."""
        query = None
        if match_phrase is not None and isinstance(match_phrase, str) and match_phrase != '{}':
            query = {
                'bool': {
                    'must': {
                        'match_phrase': json.loads(match_phrase)
                    }
                }
            }

        doc_list = []
        elastic_utils.dump_index(
            index=index,
            query=query,
            result=doc_list,
            source='d1Id,dirId,docId'.split(','),
            size=100,
            limit=10000,
        )

        return doc_list
