#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from utils import Utils

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class CorpusTransferUtils(Utils):
    """ 크롤링 결과 이동 유틸 """

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.elastic_info = {
            'host': 'http://gollum06:9201',
            'index': 'crawler-',
            'type': 'doc',
            'insert': True
        }

        self.mongodb_info = {
            'host': 'frodo',
            'port': 27018
        }

    def get_collection_list(self, db_name):
        """"""
        connect, mongodb = self.open_db(host=self.mongodb_info['host'],
                                        port=self.mongodb_info['port'],
                                        db_name=db_name)

        result = mongodb.collection_names()

        connect.close()

        return result

    def get_all_documents(self, db_name, collection_name):
        """"""
        connect, mongodb = self.open_db(host=self.mongodb_info['host'],
                                        port=self.mongodb_info['port'],
                                        db_name=db_name)

        collection = mongodb.get_collection(collection_name)
        cursor = collection.find()[:]

        result = []
        for document in cursor:
            result.append(document)

        cursor.close()
        connect.close()

        return result

    def move(self, db_name, index):
        """"""
        host = self.elastic_info['host']

        # 인덱스 생성
        doc_id_index, _ = self.get_document_id_list(host=host, index=index)

        self.elastic_info['index'] = index
        self.elastic_info['type'] = 'doc'

        bulk_size = 1000

        for collection_name in self.get_collection_list(db_name=db_name):
            if 'section' in collection_name or 'error' in collection_name:
                continue

            logging.info(msg='{}, {}'.format(db_name, collection_name))

            doc_list = self.get_all_documents(db_name=db_name, collection_name=collection_name)

            count = 0
            for doc in doc_list:
                doc_id = doc['_id']
                count += 1

                if doc_id in doc_id_index:
                    logging.info(msg='skip {:,} {}'.format(count, doc_id))
                    continue

                self.save_elastic_search_document(host=host, index=index, doc_type='doc',
                                                  document=doc, bulk_size=bulk_size, insert=True)

            self.save_elastic_search_document(host=host, index=index, doc_type='doc',
                                              document=None, bulk_size=0, insert=True)

        return

    def move_all(self):
        """"""

        db_list = """
yonhapnews_sports/
yonhapnewstv_sports/
donga_baseball/
einfomax_finance/
joins_baseball/
joins_live_baseball/
khan_baseball/
lineagem_free/
mk_sports/
mlbpark_kbo/
monoytoday_sports/
daum_3min_baseball/
daum_baseball_game_info/
daum_culture/
daum_economy/
daum_editorial/
daum_international/
daum_it/
daum_politics/
naver_kin_baseball/
daum_sports/
nate_sports/
nate_tv/
nate_opinion/
nate_photo/
nate_politics/
nate_radio/
nate_it/
naver_it/
naver_opinion/
naver_politics/
naver_sports/
naver_tv/
jisikman_app/
nate_entertainment/
daum_society/
nate_economy/
nate_international/
nate_society/
naver_economy/
naver_international/
naver_living/
naver_society/
        """

        import re

        for db_name in db_list.split('\n'):
            db_name = db_name.replace('/', '').strip()

            if db_name == '':
                continue

            index = re.sub('_', '-', db_name)

            self.move(db_name=db_name, index='crawler-{}'.format(index))

        return

    @staticmethod
    def elastic_scroll(elastic, scroll_id, index, size, query, sum_count):
        """"""
        params = {'request_timeout': 2 * 60}

        # 스크롤 아이디가 있다면 scroll 함수 호출
        if scroll_id == '':
            search_result = elastic.search(index=index, doc_type='doc', body=query, scroll='2m',
                                           size=size, params=params)
        else:
            search_result = elastic.scroll(scroll_id=scroll_id, scroll='2m', params=params)

        # 검색 결과 추출
        scroll_id = search_result['_scroll_id']

        hits = search_result['hits']

        total = hits['total']

        count = len(hits['hits'])

        sum_count += count
        logging.info(msg='{} {:,} {:,} {:,}'.format(index, count, sum_count, total))

        return hits['hits'], scroll_id, count, sum_count

    @staticmethod
    def create_elastic_index(elastic, index_name=None):
        """ elastic-search 에 인덱스를 생성한다.

        :param elastic: elastic 서버 접속 정보
        :param index_name: 생성할 인덱스 이름
        :return: True/False
        settings 정보:
            * 'number_of_shards': 샤딩 수
            * 'number_of_replicas': 리플리카 수
            * 'index.mapper.dynamic': mapping 자동 할당
        """
        if elastic is None:
            return False

        elastic.indices.create(
            index=index_name,
            body={
                'settings': {
                    'number_of_shards': 3,
                    'number_of_replicas': 3
                }
            }
        )

        return True

    def open_elastic_search(self, host, index):
        """elastic-search 에 접속한다.

        :param host: 접속 url
        :param index: 인덱스명
        :return: 접속 정보
        """
        from elasticsearch import Elasticsearch

        # target 접속
        try:
            elastic = Elasticsearch(hosts=host, timeout=30)

            if elastic.indices.exists(index) is False:
                self.create_elastic_index(elastic, index)
        except Exception as e:
            logging.error(msg='elastic-search 접속 에러: {}'.format(e))
            return None

        return elastic

    def get_document_id_list(self, host, index, use_cache=True):
        """ elastic search 에 문서 아이디 목록 조회

        :param host: elastic search 서버 주소
        :param index: 인덱스명
        :param use_cache: 캐쉬 사용
        :return: 문서 아이디 목록
        """
        filename = 'data/{}.plk'.format(index)
        if use_cache is True:
            result = self.load_index_cache(filename)

            if len(result) > 0:
                return result, filename

        elastic = self.open_elastic_search(host=host, index=index)

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
            hits, scroll_id, count, sum_count = self.elastic_scroll(
                elastic=elastic, scroll_id=scroll_id, index=index,
                size=size, query=query, sum_count=sum_count)

            for item in hits:
                document_id = item['_id']

                result[document_id] = document_id

            # 종료 조건
            if count < size:
                break

        self.save_index_cache(cache_data=result, filename=filename)

        return result, filename

    @staticmethod
    def save_index_cache(filename, cache_data):
        """"""
        import pickle

        with open(filename, 'wb') as fp:
            pickle.dump(cache_data, fp)

        return

    @staticmethod
    def load_index_cache(filename):
        """"""
        import pickle
        from os.path import isfile

        result = {}
        if isfile(filename):
            with open(filename, 'rb') as fp:
                result = pickle.load(fp)

        return result

    def push_data(self, host, index):
        """"""
        import sys
        import json

        from dateutil.parser import parse as parse_date

        # 인덱스 생성
        doc_id_index, _ = self.get_document_id_list(host=host, index=index)

        bulk_size = 1000

        count = 0
        for line in sys.stdin:
            line = line.strip()

            if line == '' or line[0] == '#':
                continue

            doc = json.loads(line)
            count += 1

            # 인덱스에 있는지 점검
            doc_id = doc['_id']
            if doc_id in doc_id_index:
                logging.info(msg='skip {:,} {}'.format(count, doc_id))
                continue

            for k in list(doc.keys()):
                if '$date' in doc[k]:
                    doc[k] = parse_date(doc[k]['$date'])

            self.save_elastic_search_document(host=host, index=index, doc_type='doc',
                                              document=doc, bulk_size=bulk_size, insert=True)

        self.save_elastic_search_document(host=host, index=index, doc_type='doc',
                                          document=None, bulk_size=0, insert=True)

        return


def init_arguments():
    """ 옵션 설정

    :return:
    """
    import textwrap
    import argparse

    description = textwrap.dedent('''\

    ''')

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=description)

    parser.add_argument('-push_data', action='store_true', default=False, help='덤프 파일에서 입력')

    parser.add_argument('-host', default='http://gollum06:9201', help='elastic search 주소')

    parser.add_argument('-index', default=None, help='인덱스명')

    parser.add_argument('-db_name', default='mlbpark_kbo', help='디비명')

    return parser.parse_args()


def main():
    """메인"""
    import re
    
    args = init_arguments()

    utils = CorpusTransferUtils()

    if args.push_data is True:
        if args.index is None and args.db_name is not None:
            args.index = 'crawler-' + re.sub('_', '-', args.db_name)
            
        utils.push_data(host=args.host, index=args.index)
    else:
        # 몽고디비에서 elastic search 로 이전
        # utils.move(db_name=args.db_name, index=args.index)
        utils.move_all()

    return


if __name__ == '__main__':
    main()
