#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
from time import sleep

import requests
from bs4 import BeautifulSoup

from module.config import Config
from module.elasticsearch_utils import ElasticSearchUtils
from module.html_parser import HtmlParser

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class QuestionDetail(object):
    """질문 상세 페이지 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_id = 'naver_kin'
        column = 'detail'

        self.parser = HtmlParser()

        self.cfg = Config(job_id=self.job_id)

        # request 헤더 정보
        self.headers = self.cfg.headers

        # html 파싱 정보
        self.parsing_info = self.cfg.parsing_info[column]

        # crawler job 정보
        self.job_info = self.cfg.job_info[column]

        self.sleep = self.job_info['sleep']

    def batch(self, list_index='crawler-naver-kin-question_list', match_phrase='{}'):
        """상세 페이지를 크롤링한다."""
        elastic_utils = ElasticSearchUtils(host=self.job_info['host'],
                                           index=self.job_info['index'], bulk_size=10)

        # 질문 목록 조회
        doc_list = self.get_doc_list(elastic_utils=elastic_utils, index=list_index,
                                     match_phrase=match_phrase)

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
            is_skip = self.exists(list_index=list_index, elastic_utils=elastic_utils,
                                  doc_id=doc_id, list_id=item['_id'])

            if is_skip is True:
                logging.info(msg='skip {} {}'.format(doc_id, self.job_info['index']))
                continue

            # 질문 상세 페이지 크롤링
            request_url = self.job_info['url_frame'].format(**q)

            resp = requests.get(url=request_url, headers=self.headers,
                                allow_redirects=True, timeout=60)

            logging.info(msg='상세 질문: {:,}/{:,} {} {}'.format(i, size, doc_id, request_url))

            # 저장
            self.save_doc(html=resp.content, elastic_utils=elastic_utils,
                          list_index=list_index,
                          doc_id=doc_id, list_id=item['_id'])

            sleep(self.sleep)

        return

    def exists(self, list_index, elastic_utils, doc_id, list_id):
        """상세 질문이 있는지 확인한다."""
        if 'question_list' in list_index:
            return False

        exists = elastic_utils.elastic.exists(index=self.job_info['index'], doc_type='doc', id=doc_id)
        if exists is True:
            elastic_utils.move_document(source_index=list_index,
                                        target_index='{}_done'.format(list_index),
                                        source_id=list_id, document_id=doc_id,
                                        host=self.job_info['host'])
            return True

        return False

    def save_doc(self, html, elastic_utils, list_index, doc_id, list_id):
        """크롤링 문서를 저장한다."""
        soup = BeautifulSoup(html, 'html5lib')

        # 이미 삭제된 질문일 경우
        if soup is not None:
            # 질문 정보 추출
            doc = self.parser.parse(html=None, soup=soup,
                                    parsing_info=self.parsing_info['values'])

            doc['_id'] = doc_id

            # 문서 저장
            elastic_utils.save_document(index=self.job_info['index'], document=doc)
            elastic_utils.flush()

            logging.info(msg='{} {}'.format(doc_id, doc['question']))

        # 질문 목록에서 완료 목록으로 이동
        elastic_utils.move_document(source_index=list_index,
                                    target_index='{}_done'.format(list_index),
                                    source_id=list_id, document_id=doc_id,
                                    host=self.job_info['host'])

        return

    @staticmethod
    def get_doc_list(elastic_utils, index, match_phrase):
        """질문 목록을 조회한다."""
        query = {
            '_source': 'd1Id,dirId,docId'.split(','),
            'size': 1000
        }

        if match_phrase is not None and isinstance(match_phrase, str) and match_phrase != '{}':
            query['query'] = {
                'bool': {
                    'must': {
                        'match_phrase': json.loads(match_phrase)
                    }
                }
            }

        result = elastic_utils.dump(index=index, query=query,
                                    only_source=False, limit=5000)
        return result
