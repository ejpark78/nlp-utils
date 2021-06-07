#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep

import requests
from bs4 import BeautifulSoup
from crawler.naver_terms.corpus_lake import CorpusLake

from crawler.naver_terms.core import TermsCore


class TermsDetail(TermsCore):
    """상세 페이지 크롤링"""

    def __init__(self, params: dict):
        super().__init__(params=params)

    def batch(self) -> None:
        """상세 페이지를 크롤링한다."""
        lake_info = {
            'type': self.params['lake_type'],
            'host': self.config['jobs']['host'],
            'index': self.config['jobs']['index'],
            'bulk_size': 5,
            'auth': self.config['jobs']['http_auth'],
            'mapping': None,
            'filename': self.params['cache'],
        }

        self.lake = CorpusLake(lake_info=lake_info)

        size = max_size = 1000

        # 검색 조건
        query = {
            'query': {
                'bool': {
                    'must': [{
                        'match': {
                            'done': 0
                        }
                    }],
                    'must_not': [{
                        'exists': {
                            'field': 'done'
                        }
                    }]
                }
            }
        }

        while size == max_size:
            # 질문 목록 조회
            term_list = self.lake.dump(**dict(index=self.config['jobs']['list_index'], limit=max_size, query=query))

            count, size = -1, len(term_list)

            for item in term_list:
                self.get_detail(
                    doc=item,
                    index=self.config['jobs']['index'],
                    list_index=self.config['jobs']['list_index'],
                    list_index_id=item['_id'],
                )

                count += 1
                sleep(self.params['sleep'])

            if size < max_size:
                break

        return

    def get_detail(self, doc: dict, index: str, list_index: str, list_index_id: str) -> bool:
        """상세 페이지를 크롤링한다."""
        request_url = doc['detail_link']
        q = self.parser.parse_url(request_url)[0]

        doc_id = f'''{q['categoryId']}-{q['cid']}-{q['docId']}'''

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
            index=index,
            doc_id=doc_id,
            doc=doc,
            base_url=request_url,
        )

        self.logger.info(msg={
            'level': 'INFO',
            'message': '상세 페이지',
            'doc_id': doc_id,
            'request_url': request_url,
        })

        # 질문 목록에 done 정보 저장
        self.lake.set_done(index=list_index, doc_id=list_index_id)

        return False

    def save_doc(self, html: str or bytes, index: str, doc: dict, doc_id: str,
                 base_url: str) -> None:
        soup = BeautifulSoup(html, 'html5lib')

        # 질문 내용이 없는 경우
        if soup is None:
            return

        detail = self.parser.parse(
            html=None,
            soup=soup,
            parsing_info=self.config['parsing']['values'],
            base_url=base_url,
        )

        doc.update({
            '_id': doc_id,
            **detail,
        })

        if '_index' in doc:
            del doc['_index']

        # 문서 저장
        self.lake.save(doc=doc, index=index)
        self.lake.flush()

        self.logger.log(msg={
            'level': 'INFO',
            'message': '문서 저장',
            'doc_id': doc_id,
            'title': doc['title'] if 'title' in doc else ''
        })

        return
