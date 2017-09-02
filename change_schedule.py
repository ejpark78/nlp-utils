#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import json
import dateutil.parser


from pymongo import MongoClient


def parse_argument():
    ''''
    옵션 설정
    '''
    import argparse

    arg_parser = argparse.ArgumentParser(description='')

    arg_parser.add_argument('-tag', help='tag', default='tag')

    return arg_parser.parse_args()


def open_db(db_name, host='gollum01', port=27017):
    '''
    몽고 디비 핸들 오픈
    '''
    connect = MongoClient('mongodb://{}:{}'.format(host, port))
    db = connect.get_database(db_name)

    return connect, db


def change_db_info():
    """
    """
    connect, db = open_db('crawler')

    collection = db.get_collection('schedule')
    cursor = collection.find({'group': 'naver_crawler'})[:]
    # cursor = collection.find({'_id': {'$regex': 'image'}})[:]
    # cursor = collection.find({'_id': 'crawler_nate_economy_2017'})[:]

    for document in cursor:
        if 'db_info' in document['parameter']:
            continue

        prev_db_info = {}
        for k in ['result_db_host', 'result_db_name', 'result_db_port', 'result_db_collection', 'domain']:
            if k in document['parameter']:
                prev_db_info[k] = document['parameter'][k]
                del document['parameter'][k]
            else:
                prev_db_info[k] = None

        upsert = False
        if 'replace' in document['parameter']:
            upsert = document['parameter']['replace']
            del document['parameter']['replace']

        document['parameter']['max_skip'] = 5000

        document['parameter']['db_info'] = {
            'mongo': {
                'host': prev_db_info['result_db_host'],
                'name': prev_db_info['result_db_name'],
                'upsert': upsert,
                'collection': prev_db_info['result_db_collection']
            },
            'mqtt': {
                '#host': 'gollum01',
                '#topic': 'crawler'
            },
            'kafka': {
                '#host': 'master',
                '#domain': 'economy',
                '#topic': 'crawler',
                '#name': prev_db_info['result_db_name']
            },
            'elastic': {
                'host': '172.20.92.49',
                'upsert': True,
                'index': prev_db_info['result_db_name'],
                'auth': [
                    'elastic',
                    'nlplab'
                ],
                'type': prev_db_info['result_db_collection']
            }
        }

        str_document = json.dumps(document, indent=4, ensure_ascii=False, sort_keys=True)
        print(str_document, flush=True)

        collection.replace_one({'_id': document['_id']}, document, upsert=True)

    cursor.close()

    connect.close()

    return


def change_volume():
    """
    """
    connect, db = open_db('crawler')

    collection = db.get_collection('schedule')
    cursor = collection.find({'docker.volume': '/home/ejpark/workspace/crawler:/crawler:ro'})[:]

    for document in cursor:

        document['docker']['volume'] = '/home/docker/crawler:/crawler:ro'

        str_document = json.dumps(document, indent=4, ensure_ascii=False, sort_keys=True)
        print(str_document, flush=True)

        # collection.replace_one({'_id': document['_id']}, document, upsert=True)

    cursor.close()

    connect.close()

    return


if __name__ == '__main__':
    change_volume()
