#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
import sys
from datetime import datetime

import urllib3
from pymongo import MongoClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)

logger = logging.getLogger()


class MongoDBUtils(object):
    """몽고 디비 유틸"""

    def __init__(self):
        """ 생성자 """

    @staticmethod
    def open(host, port, db_name):
        """ 디비에 연결한다."""
        connect = MongoClient('mongodb://{}:{}'.format(host, port))
        db = connect.get_database(db_name)

        return connect, db

    def get_collection(self, db_info, collection=None):
        """컬랙션 연결 정보를 반환한다."""
        connect, db = self.open(host=db_info['host'], port=db_info['port'], db_name=db_info['db_name'])

        if collection is None:
            if 'collection' in db_info:
                collection = db_info['collection']
            else:
                return None, None, None, None

        result = db.get_collection(collection)

        return connect, result, db_info

    def get_collection_list(self, db_info, db_name=None):
        """컬랙션 목록을 반환한다."""
        connect, db = self.open(host=db_info['host'], port=db_info['port'], db_name=db_name)

        result = []
        for collection in db.collection_names():
            if collection[0] == '_':
                continue

            result.append(collection)

        connect.close()

        return result

    def get_document_list(self, collection, db_info, field=None):
        """문서 목록을 반환한다."""
        connect, collect, _ = self.get_collection(db_info=db_info, collection=collection)

        query_filter = {'_id': 1}
        if field is not None:
            query_filter = field

        cursor = collect.find({}, query_filter)[:]

        result = []
        for document in cursor:
            # datetime 형식을 문자열로 변환
            if 'date' in document:
                if isinstance(document['date'], datetime):
                    document['date'] = '{}'.format(document['date'])

            if field is not None:
                result.append(document)
            else:
                result.append(document['_id'])

        cursor.close()
        connect.close()

        return result

    def get_document(self, collection, document_id, db_info):
        """문서를 읽어서 반환한다."""
        connect, collect, _ = self.get_collection(db_info=db_info, collection=collection)

        result = collect.find_one(filter={'_id': document_id})

        # datetime 형식을 문자열로 변환
        if result is not None and 'date' in result:
            if isinstance(result['date'], datetime):
                result['date'] = '{}'.format(result['date'])

        connect.close()

        return result

    def save_document(self, collection, document_id, document, db_info, flexible_id=False):
        """문서를 저장한다."""
        # 현재 시간 입력
        document['date'] = datetime.now()

        connect, collect, _ = self.get_collection(db_info=db_info, collection=collection)

        if flexible_id is True:
            document_id = self.get_flexible_id(db_info=db_info, collection=collection,
                                               document_id=document_id)

            document['_id'] = document_id
            collect.insert(document)

        else:
            if document['_id'] == document_id:
                collect.update({'_id': document_id}, document, upsert=True)
            else:
                collect.insert(document)

        connect.close()

        # datetime 형식을 문자열로 변환
        if document is not None and 'date' in document:
            if isinstance(document['date'], datetime):
                document['date'] = '{}'.format(document['date'])

        return document

    def get_flexible_id(self, collection, db_info, document_id):
        """"""
        import re

        document_list = self.get_document_list(collection=collection, db_info=db_info)

        count = 0
        for doc_id in document_list:
            simple_doc_id = re.sub(' \(\d+?\)$', '', doc_id)

            if document_id != simple_doc_id:
                continue

            m = re.search('\(\d+?\)$', doc_id)
            if m is not None:
                max_id = m.group(0)
                max_id = max_id.replace('(', '').replace(')', '')
                max_id = int(max_id)

                if count < max_id:
                    count = max_id

            count += 1

        result = document_id
        if count > 0:
            result = '{} ({})'.format(document_id, count)

        return result

    def move_document(self, document_id, from_collection, to_collection, db_info):
        """삭제된 문서는 '_deleted-{collection}' 컬렉션으로 이동한다. """
        time_tag = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        connect, db = self.open(host=db_info['host'], port=db_info['port'], db_name=db_info['db_name'])

        try:
            # 문서 읽기
            from_db = db.get_collection(from_collection)

            query = {'_id': document_id}

            document = from_db.find_one(filter=query)

            # 문서 삽입
            to_db = db.get_collection(to_collection)

            document['_id'] = '{}-{}'.format(document_id, time_tag)

            to_db.insert(document)

            # 문서 삭제
            from_db.remove(query)
        except Exception as e:
            print('ERROR: ', e, flush=True)
            connect.close()
            return False

        connect.close()

        return True

    def get_all_documents(self, db_info, collection):
        """전체 문서를 조회한다."""
        collection_list = [collection]
        if collection.find(',') > 0:
            collection_list = collection.split(',')

        result = []
        for group in collection_list:
            connect, collect, _ = self.get_collection(db_info=db_info, collection=group)

            cursor = collect.find({})

            for doc in cursor:
                if 'date' in doc and isinstance(doc['date'], datetime):
                    doc['date'] = '{}'.format(doc['date'])

                result.append(doc)

            cursor.close()
            connect.close()

        return result

    @staticmethod
    def save_document_list(document_list, filename):
        """전체 문서를 저장한다."""
        with bz2.open(filename, 'wb') as fp:
            for doc in document_list:
                if 'date' in doc and isinstance(doc['date'], datetime):
                    doc['date'] = '{}'.format(doc['date'])

                line = json.dumps(doc, ensure_ascii=False, sort_keys=True) + '\n'

                fp.write(line.encode('utf-8'))

        return

    def batch(self):
        """배치 작업"""
        host = 'localhost'
        port = 27018
        db_name = 'game_dictionary'
        group = 'terms'

        fp = open('data/backup.json', 'w')

        connect, db = self.open(host=host, port=port, db_name=db_name)

        collect = db.get_collection(group)

        cursor = collect.find({})

        count = 0
        for doc in cursor:
            fp.write(json.dumps(doc, ensure_ascii=False, default=self.json_serial) + '\n')
            count += 1
            print('{:,}'.format(count), end='\r', flush=True)
            if count % 100 == 0:
                fp.flush()

            if doc['name'] == '리니지m':
                doc['name'] = '리니지m'

            if doc['name'] == '게임 공통':
                doc['name'] = '게임 공통'

            collect.update({'_id': doc['_id']}, doc, upsert=True)

        cursor.close()

        connect.close()

        fp.flush()
        fp.close()

        return

    @staticmethod
    def json_serial(obj):
        """ json.dumps 의 콜백 함수로 넘겨주는 함수, 날자 형식을 문자로 반환"""
        from datetime import datetime

        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')

        raise TypeError("Type not serializable")

    def import_data(self, host, port, group, db_name):
        """데이터를 입력한다."""
        connect, db = self.open(host=host, port=port, db_name=db_name)

        collect = db.get_collection(group)

        for line in sys.stdin:
            doc = json.loads(line)

            if 'date' in doc and '$date' in doc['date']:
                doc['date'] = doc['date']['$date']

            print(doc['_id'])

            try:
                collect.insert_one(doc)
            except Exception as e:
                print(e, flush=True)

        connect.close()

        return

    def export_data(self, host, port, group, db_name):
        """데이터를 내보낸다."""
        connect, db = self.open(host=host, port=port, db_name=db_name)

        collect = db.get_collection(group)

        cursor = collect.find({})

        for doc in cursor:
            print(json.dumps(doc, ensure_ascii=False, default=self.json_serial), flush=True)

        cursor.close()

        connect.close()

        return

    def drop_group(self, host, port, group, db_name):
        """그룹을 삭제한다."""
        connect, db = self.open(host=host, port=port, db_name=db_name)

        db.drop_collection(group)

        connect.close()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('-host', default='frodo', help='')
        parser.add_argument('-port', default=27017, help='')
        parser.add_argument('-group', default='', help='')
        parser.add_argument('-db_name', default='', help='')

        parser.add_argument('-batch', action='store_true', default=False, help='')
        parser.add_argument('-import_data', action='store_true', default=False, help='')
        parser.add_argument('-export_data', action='store_true', default=False, help='')
        parser.add_argument('-drop_group', action='store_true', default=False, help='')

        return parser.parse_args()


def main():
    """메인"""
    utils = MongoDBUtils()
    args = utils.init_arguments()

    if args.batch:
        utils.batch()
        return

    if args.import_data:
        utils.import_data(host=args.host, port=args.port,
                          group=args.group, db_name=args.db_name)

    if args.export_data:
        utils.export_data(host=args.host, port=args.port,
                          group=args.group, db_name=args.db_name)

    if args.drop_group:
        utils.drop_group(host=args.host, port=args.port,
                         group=args.group, db_name=args.db_name)

    return


if __name__ == '__main__':
    main()
