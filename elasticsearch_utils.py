#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from datetime import datetime

from elasticsearch import Elasticsearch

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class ElasticSearchUtils(object):
    """"""

    def __init__(self, host, index, bulk_size=1000, insert=True, doc_type='doc'):
        """ 생성자 """
        self.host = host

        self.elastic = None

        self.index = index
        self.doc_type = doc_type

        self.bulk_data = {}
        self.bulk_size = bulk_size

        self.insert = insert

    @staticmethod
    def create_index(elastic, index=None):
        """ elastic-search 에 인덱스를 생성한다.

        :param elastic: elastic 서버 접속 정보
        :param index: 인덱스 이름
        :return: True/False
        settings 정보:
            * 'number_of_shards': 샤딩 수
            * 'number_of_replicas': 리플리카 수
            * 'index.mapper.dynamic': mapping 자동 할당
        """
        if elastic is None:
            return False

        elastic.indices.create(
            index=index,
            body={
                'settings': {
                    'number_of_shards': 3,
                    'number_of_replicas': 3
                }
            }
        )

        return True

    @staticmethod
    def convert_datetime(document):
        """ 입력받은 문서에서 데이터 타입이 datetime 를 문자열로 변환한다.

        :param document: 문서
        :return: 변환된 문서
        """
        for k in document:
            item = document[k]

            if isinstance(item, datetime):
                document[k] = item.strftime('%Y-%m-%dT%H:%M:%S')

        return document

    def open(self):
        """elastic-search 에 접속한다.

        :return: 접속 정보
        """
        # host 접속
        try:
            self.elastic = Elasticsearch(hosts=self.host, timeout=30)
        except Exception as e:
            logging.error(msg='elastic-search 접속 에러: {}'.format(e))
            return

        try:
            if self.elastic.indices.exists(self.index) is False:
                self.create_index(self.elastic, self.index)
        except Exception as e:
            logging.error(msg='elastic-search 인덱스 생성 에러: {}'.format(e))
            return

        return

    def save_document(self, document, index=None):
        """문서를 elastic-search 에 저장한다.

        :param document: 저장할 문서
        :param index: 인덱스명
        :return:
        """
        # 서버 접속
        if self.elastic is None:
            self.open()

        if index is not None:
            self.index = index

        # 버퍼링
        if document is not None:
            # 날짜 변환
            document = self.convert_datetime(document=document)

            document_id = datetime.now().strftime('%Y%m%d_%H%M%S.%f')

            if '_id' in document:
                document_id = document['_id']
                del document['_id']
            elif 'document_id' in document:
                document_id = document['document_id']

            document['document_id'] = document_id

            if self.host not in self.bulk_data:
                self.bulk_data[self.host] = []

            self.bulk_data[self.host].append({
                'update': {
                    '_index': self.index,
                    '_type': self.doc_type,
                    '_id': document_id
                }
            })

            self.bulk_data[self.host].append({
                'doc': document,
                'doc_as_upsert': self.insert
            })

            # 버퍼링
            if self.bulk_size * 2 > len(self.bulk_data[self.host]):
                return True

        # 버퍼 크기 확인
        if self.host not in self.bulk_data or len(self.bulk_data[self.host]) == 0:
            return True

        # 버퍼 밀어내기
        self.flush()

        return True

    def flush(self):
        """"""
        if self.elastic is None:
            return None

        size = -1
        response = None
        doc_id_list = []

        params = {'request_timeout': 2 * 60}

        try:
            response = self.elastic.bulk(index=self.index, body=self.bulk_data[self.host],
                                         refresh=True, params=params)

            size = len(self.bulk_data[self.host])
            doc_id_list = []
            for doc in self.bulk_data[self.host]:
                if 'update' in doc and '_id' in doc['update']:
                    doc_id_list.append(doc['update']['_id'])

            self.bulk_data[self.host] = []
        except Exception as e:
            msg = 'elastic-search 저장 에러: {}'.format(e)
            logging.error(msg=msg)

        try:
            error = '성공'
            if response['errors'] is True:
                error = '에러'

            msg = 'elastic-search 저장 결과: {}, {:,}'.format(error, int(size / 2))
            logging.info(msg=msg)

            if len(doc_id_list) > 0:
                for doc_id in doc_id_list[:10]:
                    msg = '{}/{}/{}/{}?pretty'.format(self.host, self.index, self.doc_type, doc_id)
                    logging.info(msg=msg)
        except Exception as e:
            msg = 'elastic-search logging 에러: {}'.format(e)
            logging.error(msg=msg)

        return

    def scroll(self, scroll_id, index, size, query, sum_count):
        """"""
        params = {
            'request_timeout': 2 * 60
        }

        # 스크롤 아이디가 있다면 scroll 함수 호출
        if scroll_id == '':
            search_result = self.elastic.search(index=index, doc_type='doc', body=query, scroll='2m',
                                                size=size, params=params)
        else:
            search_result = self.elastic.scroll(scroll_id=scroll_id, scroll='2m', params=params)

        # 검색 결과 추출
        scroll_id = search_result['_scroll_id']

        hits = search_result['hits']

        total = hits['total']
        count = len(hits['hits'])

        sum_count += count
        logging.info(msg='{} {:,} {:,} {:,}'.format(index, count, sum_count, total))

        return hits['hits'], scroll_id, count, sum_count

    def get_id_list(self, index, use_cache=False):
        """ elastic search 에 문서 아이디 목록을 조회한다.

        :param index: 인덱스명
        :param use_cache: 캐쉬 사용
        :return: 문서 아이디 목록
        """
        filename = 'data/{}.plk'.format(index)
        if use_cache is True:
            result = self.load_cache(filename)

            if len(result) > 0:
                return result, filename

        # 한번에 가져올 문서수
        size = 5000

        count = 1
        sum_count = 0
        scroll_id = ''

        result = {}

        query = {
            '_source': '',
        }

        while count > 0:
            hits, scroll_id, count, sum_count = self.scroll(
                scroll_id=scroll_id, index=index,
                size=size, query=query, sum_count=sum_count)

            for item in hits:
                document_id = item['_id']

                result[document_id] = document_id

            # 종료 조건
            if count < size:
                break

        if use_cache is True:
            self.save_cache(cache_data=result, filename=filename)

        return result, filename

    @staticmethod
    def save_cache(filename, cache_data):
        """"""
        import pickle

        with open(filename, 'wb') as fp:
            pickle.dump(cache_data, fp)

        return

    @staticmethod
    def load_cache(filename):
        """"""
        import pickle
        from os.path import isfile

        result = {}
        if isfile(filename):
            with open(filename, 'rb') as fp:
                result = pickle.load(fp)

        return result

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('-test', action='store_true', default=False, help='')

        return parser.parse_args()
