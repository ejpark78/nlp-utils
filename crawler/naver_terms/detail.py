#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from time import sleep

import requests
from bs4 import BeautifulSoup

from crawler.naver_terms.core import TermsCore
from crawler.utils.es import ElasticSearchUtils


class TermsDetail(TermsCore):
    """상세 페이지 크롤링"""

    def __init__(self, params: dict):
        super().__init__(params=params)

    def batch(self) -> None:
        """상세 페이지를 크롤링한다."""
        es = ElasticSearchUtils(
            host=self.config['jobs']['host'],
            index=self.config['jobs']['index'],
            bulk_size=10,
            http_auth=self.config['jobs']['http_auth'],
        )

        size = max_size = 1000

        while size == max_size:
            # 질문 목록 조회
            doc_list = self.get_doc_list(
                elastic_utils=es,
                index=self.config['jobs']['list_index'],
                match_phrase='{}',
                size=max_size,
            )

            count, size = -1, len(doc_list)

            for item in doc_list:
                self.get_detail(
                    doc=item,
                    list_id=item['_id'],
                    list_index=self.config['jobs']['list_index'],
                    elastic_utils=es,
                )

                count += 1
                sleep(self.params['sleep'])

            if size < max_size:
                break

        return

    def get_detail(self, doc: dict, elastic_utils: ElasticSearchUtils, list_index: str, list_id: str) -> bool:
        """상세 페이지를 크롤링한다."""
        request_url = doc['detail_link']
        q = self.parser.parse_url(request_url)[0]

        doc_id = f'''{q['categoryId']}-{q['cid']}-{q['docId']}'''

        # 이미 받은 항목인지 검사
        is_skip = elastic_utils.exists(
            index=self.config['jobs']['index'],
            list_index=list_index,
            doc_id=doc_id,
            list_id=list_id,
            merge_column='category',
        )

        if is_skip is True:
            self.logger.info(msg={
                'level': 'INFO',
                'message': 'skip',
                'index': self.config['jobs']['index'],
                'doc_id': doc_id,
            })

            return True

        # 질문 상세 페이지 크롤링
        try:
            resp = requests.get(
                url=request_url,
                headers=self.headers['mobile'],
                allow_redirects=True,
                timeout=60,
                verify=False
            )
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '상세 페이지 조회 에러',
                'exception': str(e),
            })

            sleep(10)
            return False

        # 저장
        self.save_doc(
            html=resp.content,
            elastic_utils=elastic_utils,
            list_index=list_index,
            list_doc=doc,
            doc_id=doc_id,
            list_id=list_id,
            base_url=request_url,
        )

        self.logger.info(msg={
            'level': 'INFO',
            'message': '상세 페이지',
            'doc_id': doc_id,
            'request_url': request_url,
        })

        return False

    def save_doc(self, html: str, elastic_utils: ElasticSearchUtils, list_index: str, list_doc: dict, doc_id: str,
                 list_id: str, base_url: str) -> None:
        soup = BeautifulSoup(html, 'html5lib')

        # 질문 내용이 있는 경우
        if soup is None:
            return

        detail = self.parser.parse(
            html=None,
            soup=soup,
            parsing_info=self.config['parsing']['values'],
            base_url=base_url,
        )

        doc = {
            **list_doc,
            **detail,
            '_id': doc_id,
        }

        if '_index' in doc:
            del doc['_index']

        # 문서 저장
        elastic_utils.save_document(index=self.config['jobs']['index'], document=doc)
        elastic_utils.flush()

        self.logger.log(msg={
            'level': 'INFO',
            'message': '문서 저장',
            'doc_id': doc_id,
            'url': elastic_utils.get_doc_url(index=self.config['jobs']['index'], document_id=doc_id),
            'title': doc['title'] if 'title' in doc else ''
        })

        # 질문 목록에서 완료 목록으로 이동
        elastic_utils.move_document(
            source_index=list_index,
            target_index=f'{list_index}_done',
            source_id=list_id,
            document_id=doc_id,
            merge_column='category',
        )

        return

    @staticmethod
    def get_doc_list(elastic_utils: ElasticSearchUtils, index: str, match_phrase: str, size: int) -> list:
        """질문 목록을 조회한다."""
        query = {
            'size': size
        }

        if match_phrase is not None and isinstance(match_phrase, str) and match_phrase != '{}':
            query['query'] = {
                'bool': {
                    'must': {
                        'match_phrase': json.loads(match_phrase)
                    }
                }
            }

        result = []
        elastic_utils.dump_index(
            index=index,
            query=query,
            limit=5000,
            result=result,
        )
        return result
