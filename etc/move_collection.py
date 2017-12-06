#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


def open_db(db_name, host='frodo', port=27018):
    """
    몽고 디비 핸들 오픈
    """
    connect = MongoClient('mongodb://{}:{}'.format(host, port))
    db = connect.get_database(db_name)

    return connect, db


def move_dbs():
    """
    A collection 에서 B collection 으로 문서 이동
    :return:
    """
    section_name = 'esports'

    db_name = 'naver_esports'
    target_db_name = 'naver_sports'

    connect, db = open_db(db_name)
    target_connect, target_db = open_db(target_db_name)

    for collection_name in sorted(db.collection_names(), reverse=True):
        print(collection_name, flush=True)

        collection = db.get_collection(collection_name)
        target_collection = target_db.get_collection(collection_name)

        cursor = collection.find({}, no_cursor_timeout=True)

        count = 0
        for document in cursor:
            if '=' in document['_id']:
                document['_id'] = document['_id'].split('=', maxsplit=1)[1]

            section_list = [section_name]
            if 'section' in document and document['section'] != '':
                section_list += document['section'].split(',')

            document['section'] = ','.join(list(set(section_list)))

            try:
                target_collection.insert_one(document)
            except DuplicateKeyError:
                prev_doc = target_collection.find_one({'_id': document['_id']}, {'section': 1})

                section_list += prev_doc['section'].split(',')

                document['section'] = ','.join(list(set(section_list)))
                target_collection.replace_one({'_id': document['_id']}, document)

            count += 1
            if count % 1000 == 0:
                print('.', end='', flush=True)

        cursor.close()
        print('\nTotal: {:,}\n'.format(count), flush=True)

    connect.close()
    target_connect.close()

    return


if __name__ == '__main__':
    move_dbs()
