#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

import requests
from bs4 import BeautifulSoup
from time import sleep

from crawler.web_news.base import WebNewsBase
from crawler.utils.es import ElasticSearchUtils


class TermDetail(WebNewsBase):
    """상세 페이지 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_category = 'naver'
        self.job_id = 'naver_terms'
        self.column = 'detail'

        self.update_config(filename=None, job_id=self.job_id, job_category=self.job_category, column=self.env.column)

    def batch(self):
        """전체 상세 페이지를 크롤링한다."""
        list_index = self.job_info['list_index']

        elastic_utils = ElasticSearchUtils(
            host=self.job_info['host'],
            index=self.job_info['index'],
            bulk_size=10,
            http_auth=self.job_info['http_auth'],
        )

        max_size = 1000
        size = max_size

        while size == max_size:
            # 질문 목록 조회
            doc_list = self.get_doc_list(
                elastic_utils=elastic_utils,
                index=list_index,
                match_phrase='{}',
                size=max_size,
            )

            count = -1
            size = len(doc_list)

            for item in doc_list:
                self.get_detail(
                    doc=item['_source'],
                    list_id=item['_id'],
                    list_index=list_index,
                    elastic_utils=elastic_utils,
                )

                count += 1
                sleep(self.sleep_time)

            if size < max_size:
                break

        return

    def get_detail(self, doc, elastic_utils, list_index, list_id):
        """상세 페이지를 크롤링한다."""
        del doc['document_id']

        request_url = doc['detail_link']
        q = self.parser.parse_url(request_url)[0]

        doc_id = '{categoryId}-{cid}-{docId}'.format(
            docId=q['docId'],
            cid=q['cid'],
            categoryId=q['categoryId'],
        )

        # 이미 받은 항목인지 검사
        is_skip = elastic_utils.exists(
            index=self.job_info['index'],
            list_index=list_index,
            doc_id=doc_id,
            list_id=list_id,
            merge_column='category',
        )

        if is_skip is True:
            self.logger.info(msg={
                'level': 'INFO',
                'message': 'skip',
                'index': self.job_info['index'],
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
            return

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

    def save_doc(self, html, elastic_utils, list_index, list_doc, doc_id, list_id, base_url):
        """크롤링 문서를 저장한다."""
        soup = BeautifulSoup(html, 'html5lib')

        # 질문 내용이 있는 경우
        if soup is not None:
            trace_tag = self.parsing_info['trace']['tag']

            doc = {
                '_id': doc_id,
                '_list_doc': list_doc
            }

            for trace in trace_tag:
                if 'attribute' not in trace:
                    trace['attribute'] = None

                if 'select' in trace:
                    # css select 인 경우
                    item_list = soup.select(trace['select'])
                else:
                    # 기존 방식
                    item_list = soup.find_all(trace['name'], trace['attribute'])

                for item in item_list:
                    # html 본문에서 값 추출
                    unit = self.parser.parse(
                        html=None,
                        soup=item,
                        parsing_info=self.parsing_info['values'],
                        base_url=base_url,
                    )

                    html_key = self.parsing_info['trace']['key']
                    unit[html_key] = str(item).replace('\t', '')

                    if html_key in doc:
                        unit[html_key] += doc[html_key]

                    doc.update(unit)

            # 문서 저장
            elastic_utils.save_document(index=self.job_info['index'], document=doc)
            elastic_utils.flush()

            msg = {
                'level': 'INFO',
                'message': '문서 저장',
                'doc_id': doc_id,
                'url': elastic_utils.get_doc_url(document_id=doc_id),
            }

            if 'title' in doc:
                msg['title'] = doc['title']

            self.logger.log(msg=msg)

        # 질문 목록에서 완료 목록으로 이동
        elastic_utils.move_document(
            source_index=list_index,
            target_index='{}_done'.format(list_index),
            source_id=list_id,
            document_id=doc_id,
            merge_column='category',
        )

        return

    @staticmethod
    def get_doc_list(elastic_utils, index, match_phrase, size):
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

        result = elastic_utils.dump(
            index=index,
            query=query,
            limit=5000,
            only_source=False,
        )
        return result
