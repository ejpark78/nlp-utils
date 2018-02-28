#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from pymongo import MongoClient


def parse_argument():
    """
    옵션 설정
    :return:
    """
    import argparse

    arg_parser = argparse.ArgumentParser(description='')

    arg_parser.add_argument('-tag', help='tag', default='tag')

    return arg_parser.parse_args()


def open_db(db_name, host='frodo', port=27018):
    """
    몽고 디비 핸들 오픈
    """
    connect = MongoClient('mongodb://{}:{}'.format(host, port))
    db = connect.get_database(db_name)

    return connect, db


def change_db_info():
    """

    :return:
    """
    from datetime import datetime

    connect, db = open_db('crawler')

    collection = db.get_collection('schedule')

    cursor = collection.find({'sleep': {'$exists': 1}})[:]

    date = datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
    fp = open('backup-{}.json'.format(date), 'a')

    for document in cursor:
        # 백업
        str_document = json.dumps(document, indent=4, ensure_ascii=False, sort_keys=True)
        fp.write(str_document + '\n\n')

        document_id = document['_id']
        print(document_id, flush=True)

        document['schedule']['sleep'] = document['sleep']
        del document['sleep']

        str_document = json.dumps(document, indent=4, ensure_ascii=False, sort_keys=True)
        print(str_document, flush=True)

        # collection.replace_one({'_id': document['_id']}, document, upsert=True)

    fp.flush()
    fp.close()

    cursor.close()

    connect.close()

    return


if __name__ == '__main__':
    change_db_info()
