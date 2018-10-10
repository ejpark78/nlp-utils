#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
from datetime import datetime

import urllib3
from pymongo import MongoClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class MongoDBUtils(object):
    """"""

    def __init__(self):
        """ 생성자 """
        pass

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
        """컬랙션 목록을 반환한다.

        :param db_info: 디비 접속 정보
        :param db_name: 디비명
        :return: 폴더 목록
        """
        connect, db = self.open(host=db_info['host'], port=db_info['port'], db_name=db_name)

        result = []
        for collection in db.collection_names():
            if collection[0] == '_':
                continue

            result.append(collection)

        connect.close()

        return result

    def get_document_list(self, collection, db_info, field=None):
        """문서 목록을 반환한다.

        :param collection: 컬랙션명
        :param field: 컬럼 목록
        :param db_info: 디비 접속 정보
        :return: 컬랙션 목록
        """
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
        """문서를 읽어서 반환한다.

        :param collection: 컬랙션명
        :param document_id: 문서 아이디
        :param db_info: 디비 접속 정보
        :return: 문서 내용
        """
        connect, collect, _ = self.get_collection(db_info=db_info, collection=collection)

        result = collect.find_one(filter={'_id': document_id})

        # datetime 형식을 문자열로 변환
        if result is not None and 'date' in result:
            if isinstance(result['date'], datetime):
                result['date'] = '{}'.format(result['date'])

        connect.close()

        return result

    def save_document(self, collection, document_id, document, db_info, flexible_id=False):
        """문서를 저장한다.

        :param collection: 컬랙션명
        :param document_id: 문서 아이디
        :param document: 문서
        :param db_info: 디비 접속 정보
        :param flexible_id: 중복 아이디 처리 (1) (2) ... 등을 붙인다.
        :return:
        """
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
        """"""
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
        """"""
        with bz2.open(filename, 'wb') as fp:
            for doc in document_list:
                if 'date' in doc and isinstance(doc['date'], datetime):
                    doc['date'] = '{}'.format(doc['date'])

                line = json.dumps(doc, ensure_ascii=False, sort_keys=True) + '\n'

                fp.write(line.encode('utf-8'))

        return
