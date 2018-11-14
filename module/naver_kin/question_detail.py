#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
from time import sleep

import requests

from module.common_utils import CommonUtils
from module.elasticsearch_utils import ElasticSearchUtils
from module.html_parser import HtmlParser
from module.config import Config

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
        self.common_utils = CommonUtils()
        self.parser = HtmlParser()

        cfg = Config(job_id=self.job_id)

        self.headers = cfg.headers

        self.job_info = cfg.job_info['detail']
        self.parsing_info = cfg.parsing_info['values']

    def get_detail(self, index='crawler-naver-kin-question_list', match_phrase='{"fullDirNamePath": "주식"}'):
        """질문/답변 상세 페이지를 크롤링한다."""
        from bs4 import BeautifulSoup

        url_frame = self.job_info['url_frame']

        delay = 5
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

        elastic_utils = ElasticSearchUtils(host=self.job_info['host'],
                                           index=self.job_info['index'], bulk_size=10)

        question_list = elastic_utils.dump_documents(index=index, query=query, only_source=False, limit=5000)

        i = -1
        size = len(question_list)

        for item in question_list:
            question = item['_source']

            # 문서 아이디 생성
            if 'd1Id' not in question:
                question['d1Id'] = str(question['dirId'])[0]

            i += 1
            doc_id = '{}-{}-{}'.format(question['d1Id'], question['dirId'], question['docId'])

            if 'question_list' not in index:
                # 이미 받은 질문인지 검사
                exists = elastic_utils.elastic.exists(index=self.job_info['index'], doc_type='doc', id=doc_id)
                if exists is True:
                    logging.info(msg='skip {} {}'.format(doc_id, self.job_info['index']))

                    elastic_utils.move_document(source_index=index, target_index='{}_done'.format(index),
                                                source_id=item['_id'], document_id=doc_id,
                                                host=self.job_info['host'])
                    continue

            # url 생성
            request_url = url_frame.format(**question)

            # 질문 상세 페이지 크롤링
            logging.info(msg='상세 질문: {:,}/{:,} {} {}'.format(i, size, doc_id, request_url))
            resp = requests.get(url=request_url, headers=self.headers,
                                allow_redirects=True, timeout=60)

            # 저장
            soup = BeautifulSoup(resp.content, 'html5lib')

            # 이미 삭제된 질문일 경우
            if soup is None:
                elastic_utils.move_document(source_index=index, target_index='{}_done'.format(index),
                                            source_id=item['_id'], document_id=doc_id,
                                            host=self.job_info['host'])
                continue

            # 질문 정보 추출
            detail_doc = self.parser.parse(html=None, soup=soup,
                                           parsing_info=self.parsing_info)

            detail_doc['_id'] = doc_id

            elastic_utils.save_document(index=self.job_info['host'], document=detail_doc)
            elastic_utils.flush()

            elastic_utils.move_document(source_index=index, target_index='{}_done'.format(index),
                                        source_id=item['_id'], document_id=doc_id,
                                        host=self.job_info['host'])

            self.common_utils.print_message(msg={
                'doc_id': doc_id,
                'question': detail_doc['question']
            })

            sleep(delay)

        return
