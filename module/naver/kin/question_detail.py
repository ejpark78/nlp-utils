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

from module.crawler_base import CrawlerBase
from module.utils.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class QuestionDetail(CrawlerBase):
    """질문 상세 페이지 크롤링"""

    def __init__(self, args):
        """ 생성자 """
        super().__init__()

        self.job_category = 'naver'
        self.job_id = 'naver_kin'
        self.column = 'detail'

        self.sleep_time = args.sleep

    def daemon(self, column, match_phrase='{}'):
        """데몬으로 실행"""
        while True:
            self.batch(column=column, match_phrase=match_phrase)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '데몬 슬립',
                'sleep_time': 60,
            })

            sleep(self.sleep_time)

    def batch(self, column, match_phrase):
        """상세 페이지를 크롤링한다."""
        self.update_config()

        elastic_utils = ElasticSearchUtils(
            host=self.job_info['host'],
            index=self.job_info['index'],
            bulk_size=10,
            http_auth=self.job_info['http_auth'],
        )

        if column == 'question':
            index = 'crawler-naver-kin-question_list'
        else:
            index = 'crawler-naver-kin-answer_list'

        # 질문 목록 조회
        doc_list = self.get_doc_list(
            index=index,
            elastic_utils=elastic_utils,
            match_phrase=match_phrase,
        )

        i = -1
        size = len(doc_list)

        for item in doc_list:
            q = item['_source']

            # 문서 아이디 생성
            if 'd1Id' not in q:
                q['d1Id'] = str(q['dirId'])[0]

            i += 1
            doc_id = '{}-{}-{}'.format(q['d1Id'], q['dirId'], q['docId'])

            # 이미 받은 항목인지 검사
            if index.find('question_list') > 0 or index.find('answer_list') > 0:
                is_skip = elastic_utils.exists(
                    index=self.job_info['index'],
                    list_index=index,
                    doc_id=doc_id,
                    list_id=item['_id'],
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
            request_url = self.job_info['url_frame'].format(**q)

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
                index=index,
                doc_id=doc_id,
                list_id=item['_id'],
                base_url=request_url,
                elastic_utils=elastic_utils,
            )

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '데몬 슬립',
                'sleep_time': self.sleep_time,
            })

            sleep(self.sleep_time)

        return

    def save_doc(self, resp, elastic_utils, index, doc_id, list_id, base_url):
        """크롤링 문서를 저장한다."""
        soup, encoding = self.get_encoding_type(resp.text)

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
                parsing_info=self.parsing_info['values'],
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
                'doc_url': '{host}/{index}/_doc/{id}?pretty'.format(
                    host=elastic_utils.host,
                    index=elastic_utils.index,
                    id=doc_id,
                )
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
    def get_doc_list(elastic_utils, index, match_phrase):
        """질문 목록을 조회한다."""
        query = {
            '_source': 'd1Id,dirId,docId'.split(','),
            'size': 100000
        }

        if match_phrase is not None and isinstance(match_phrase, str) and match_phrase != '{}':
            query['query'] = {
                'bool': {
                    'must': {
                        'match_phrase': json.loads(match_phrase)
                    }
                }
            }

        result = elastic_utils.dump(
            index=index,
            query=query,
            only_source=False,
            limit=5000,
        )
        return result
