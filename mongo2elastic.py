#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import re
import sys

from dateutil.parser import parse as parse_date

from elasticsearch_utils import ElasticSearchUtils
from mongodb_utils import MongoDBUtils

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class Mongo2ElasticUtils(object):
    """ 크롤링 결과 이동 유틸 """

    def __init__(self):
        """ 생성자 """

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
        mongodb_utils = MongoDBUtils()

        connect, mongodb = mongodb_utils.open(
            host=self.mongodb_info['host'], port=self.mongodb_info['port'], db_name=db_name)

        result = mongodb.collection_names()

        connect.close()

        return result

    def get_all_documents(self, db_name, collection_name):
        """"""
        mongodb_utils = MongoDBUtils()

        connect, mongodb = mongodb_utils.open(
            host=self.mongodb_info['host'], port=self.mongodb_info['port'], db_name=db_name)

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
        elastic_utils = ElasticSearchUtils(host=host, index=index)
        doc_id_index, _ = elastic_utils.get_id_list(index=index, use_cache=True)

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

                elastic_utils.save_document(index=index, document=doc)

            elastic_utils.flush()

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
        for db_name in db_list.split('\n'):
            db_name = db_name.replace('/', '').strip()

            if db_name == '':
                continue

            index = re.sub('_', '-', db_name)

            self.move(db_name=db_name, index='crawler-{}'.format(index))

        return

    @staticmethod
    def push_data(host, index):
        """"""
        elastic_utils = ElasticSearchUtils(host=host, index=index)

        # 인덱스 생성
        doc_id_index, _ = elastic_utils.get_id_list(index=index, use_cache=True)

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

            elastic_utils.save_document(index=index, document=doc)

        elastic_utils.flush()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('-push_data', action='store_true', default=False, help='덤프 파일에서 입력')

        parser.add_argument('-host', default='http://gollum06:9201', help='elastic search 주소')
        parser.add_argument('-index', default=None, help='인덱스명')
        parser.add_argument('-db_name', default='mlbpark_kbo', help='디비명')

        return parser.parse_args()


def main():
    """메인"""
    import re

    utils = Mongo2ElasticUtils()
    args = utils.init_arguments()

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
