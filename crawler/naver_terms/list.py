#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep

import requests
import urllib3
from bs4 import BeautifulSoup

from crawler.naver_terms.core import TermsCore
from crawler.naver_terms.corpus_lake import CorpusLake

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class TermsList(TermsCore):
    """백과사전 목록 크롤링"""

    def __init__(self, params: dict):
        super().__init__(params=params)

        self.status = {}

    def batch(self) -> None:
        """카테고리 하위 목록을 크롤링한다."""
        lake_info = {
            'type': self.params['lake_type'],
            'host': self.config['jobs']['host'],
            'index': self.config['jobs']['list_index'],
            'bulk_size': 20,
            'auth': self.config['jobs']['http_auth'],
            'mapping': self.config['index_mapping'],
            'filename': self.params['cache']
        }

        self.lake = CorpusLake(lake_info=lake_info)

        category_id = None

        # 카테고리 하위 목록을 크롤링한다.
        for category in self.config['jobs']['category']:
            self.status = {
                'start': self.params['list_start'],
                'end': self.params['list_end'],
                'step': self.params['list_step'],
            }

            if len(self.job_sub_category) > 0 and category['name'] not in self.job_sub_category:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': 'skip 카테고리',
                    'category': category['name'],
                })
                continue

            if category_id is not None and category['id'] != category_id:
                continue

            category_id = None
            self.get_term_list(category=category)

        return

    def get_term_list(self, category: dict) -> None:
        """용어 목록을 크롤링한다."""
        url = self.config['jobs']['url_frame']

        # start 부터 end 까지 반복한다.
        for page in range(self.status['start'], self.status['end'], self.status['step']):
            # 쿼리 url 생성
            query_url = url.format(categoryId=category['id'], page=page)

            # 페이지 조회
            try:
                resp = requests.get(
                    url=query_url,
                    headers=self.headers['mobile'],
                    allow_redirects=True,
                    timeout=60,
                    verify=False
                )
            except Exception as e:
                self.logger.error(msg={
                    'e': str(e)
                })
                sleep(10)
                continue

            # 문서 저장
            is_stop = self.save_doc(
                html=resp.content,
                base_url=url,
                category_name=category['name'],
            )

            # 현재 크롤링 위치 저장
            self.status['start'] = page
            self.status['category'] = category

            # 현재 상태 로그 표시
            self.logger.info(msg={
                'name': category['name'],
                'page': page
            })

            if is_stop is True:
                break

            sleep(self.params['sleep'])

        return

    def save_doc(self, html: str or bytes, category_name: str, base_url: str) -> bool:
        """크롤링한 문서를 저장한다."""
        soup = BeautifulSoup(html, 'html5lib')

        trace_tag = self.config['parsing']['trace']['value']

        for trace in trace_tag:
            if 'select' in trace:
                # css select 인 경우
                item_list = soup.select(trace['select'])
            else:
                # 기존 방식
                item_list = soup.find_all(trace['name'], trace['attribute'])

            for item in item_list:
                # html 본문에서 값 추출
                doc = self.parser.parse(
                    html=None,
                    soup=item,
                    parsing_info=self.config['parsing']['values'],
                    base_url=base_url,
                )

                # url 파싱
                q = self.parser.parse_url(doc['detail_link'])[0]

                # 문서 메타정보 등록
                doc['_id'] = f'''{q['cid']}-{q['docId']}'''

                doc['category'] = category_name

                # 저장 로그 표시
                self.logger.log(msg={
                    'MESSAGE': '신규 용어',
                    'category_name': category_name,
                    '_id': doc['_id'],
                    'name': doc['name'],
                    'define': doc['define'][:30]
                })

                self.history.add(doc['_id'])

                # 이전에 수집한 문서와 병합
                doc = self.lake.merge(doc=doc, **dict(
                    index=self.config['jobs']['list_index'],
                    column=['category']
                ))

                self.lake.save(doc=doc, **dict(index=self.config['jobs']['list_index']))

            self.lake.flush()

        return False
