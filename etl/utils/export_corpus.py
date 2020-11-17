#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
import ssl
from datetime import datetime

import urllib3
from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context
from tqdm.autonotebook import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class ExportCorpus(object):
    """코퍼스 Export"""

    def __init__(self, host, index=None, http_auth=None):
        """ 생성자 """
        self.host = host

        self.elastic = None
        self.http_auth = http_auth

        self.index = index

        if self.host is not None:
            self.open()

    def open(self):
        """서버에 접속한다."""
        ssl_context = create_ssl_context()

        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # host 접속
        try:
            self.elastic = Elasticsearch(
                hosts=self.host,
                timeout=30,
                http_auth=self.http_auth,
                ssl_context=ssl_context,
            )
        except Exception as e:
            logging.error(msg='서버 접속 에러: ' + str(e))
            return

        return

    def scroll(self, index, scroll_id, query, size=1000):
        """스크롤 API를 호출한다."""
        if index is None:
            index = self.index

        params = {
            'request_timeout': 2 * 60
        }

        # 스크롤 아이디가 있다면 scroll 함수 호출
        if scroll_id == '':
            search_result = self.elastic.search(
                index=index,
                body=query,
                scroll='2m',
                size=size,
                params=params,
            )
        else:
            search_result = self.elastic.scroll(
                scroll='2m',
                params=params,
                scroll_id=scroll_id,
            )

        # 검색 결과 추출
        scroll_id = search_result['_scroll_id']

        hits = search_result['hits']

        total = hits['total']
        if isinstance(total, dict) and 'value' in total:
            total = total['value']

        count = len(hits['hits'])

        return hits['hits'], scroll_id, count, total

    def dump_data(self, index, query=None, source=None, date_range=None, size=1000):
        """데이터를 서버에서 덤프 받는다."""
        if query is None:
            query = {}

        if date_range is not None and date_range.find('~') > 0:
            start, end = date_range.split('~')

            query = {
                'query': {
                    'bool': {
                        'must': [
                            {
                                'range': {
                                    'curl_date': {
                                        'format': 'yyyy-MM-dd',
                                        'gte': start,
                                        'lte': end
                                    }
                                }
                            }
                        ]
                    }
                }
            }

        if source is not None and len(source) > 0:
            query['_source'] = source

        self.index = index

        count = 1
        sum_count = 0
        scroll_id = ''

        pbar = None

        result = []

        while count > 0:
            hits, scroll_id, count, total = self.scroll(
                index=index,
                scroll_id=scroll_id,
                size=size,
                query=query,
            )

            if pbar is None:
                pbar = tqdm(total=total)
                pbar.set_description(index)

            pbar.update(count)

            sum_count += count

            for item in hits:
                result.append(item['_source'])

            # 종료 조건
            if count < size:
                break

        pbar.close()
        return result

    def get_index_list(self):
        """모든 인덱스 목록을 반환한다."""
        return [v for v in self.elastic.indices.get('*') if v[0] != '.']

    def batch(self, index_list, source, date_range):
        """배치 작업을 수행한다."""
        for index in tqdm(index_list, desc='인덱스 덤프'):
            document_list = self.dump_data(
                index=index,
                source=source,
                date_range=date_range,
            )

            filename = '{}.json.bz2'.format(index)

            with bz2.open(filename, 'wb') as fp:
                for doc in tqdm(document_list, desc=index):
                    if 'date' in doc and isinstance(doc['date'], datetime):
                        doc['date'] = str(doc['date'])

                    line = json.dumps(doc, ensure_ascii=False) + '\n'
                    fp.write(line.encode('utf-8'))

        return


def main():
    """"""
    # date_range = '2019-04-01~2019-04-02'
    date_range = ''

    # source = ['document_id', 'title', 'date', 'source', 'pos_tagged', 'paper']
    source = None

    index_list = [
        'crawler-naver-terms-list',
        'crawler-naver-terms-list_done',
        'crawler-naver-terms-detail',
    ]

    ExportCorpus(host='https://corpus.ncsoft.com:9200').batch(
        index_list=index_list,
        source=source,
        date_range=date_range,
    )
    return


if __name__ == '__main__':
    main()
