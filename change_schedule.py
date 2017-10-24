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


def open_db(db_name, host='frodo', port=27018):
    """
    몽고 디비 핸들 오픈
    """
    connect = MongoClient('mongodb://{}:{}'.format(host, port))
    db = connect.get_database(db_name)

    return connect, db


def change_db_info():
    """
    """
    connect, db = open_db('crawler')

    collection = db.get_collection('schedule')
    # cursor = collection.find({'group': 'naver_crawler'})[:]
    # cursor = collection.find({'_id': {'$regex': 'image'}})[:]
    # cursor = collection.find({'_id': 'crawler_nate_economy_2017'})[:]
    # cursor = collection.find({'group': {'$regex': 'jisikman'}})[:]
    # cursor = collection.find({'group': {'$regex': 'mlbpark_'}})[:]
    # cursor = collection.find({'parameter.db_info.mongo.host': 'frodo01'})[:]
    # cursor = collection.find({'_id': 'crawler_lineagem_free_latest'})[:]
    cursor = collection.find({'docker.network': 'hadoop-net'})[:]

    for document in cursor:
        # upsert = False
        # if 'replace' in document['parameter']:
        #     upsert = document['parameter']['replace']
        #     del document['parameter']['replace']

        print(document['_id'], flush=True)
        # db_info = document['parameter']['db_info']
        #
        # document['parameter']['max_skip'] = 5000
        # document['parameter']['db_info'] = {
        #     'mongo': {
        #         'host': 'frodo01',
        #         'port': 27018,
        #         'name': db_info['mongo']['name'],
        #         'upsert': upsert
        #     },
        #     'mqtt': {
        #         '#host': 'gollum',
        #         '#topic': 'crawler'
        #     },
        #     'kafka': {
        #         '#host': 'master',
        #         '#domain': 'economy',
        #         '#topic': 'crawler',
        #         '#name': ''
        #     },
        #     'elastic': {
        #         'host': 'frodo',
        #         'upsert': True,
        #         'index': db_info['mongo']['name'],
        #         'auth': [
        #             'elastic',
        #             'nlplab'
        #         ]
        #     }
        # }

        if 'network' in document['docker']:
            del document['docker']['network']

        document['docker']['volume'] = '/data/nlp_home/docker/crawler:/crawler:ro'

        str_document = json.dumps(document, indent=4, ensure_ascii=False, sort_keys=True)
        print(str_document, flush=True)

        # collection.replace_one({'_id': document['_id']}, document, upsert=True)

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


def change_network():
    """
    """
    connect, db = open_db('crawler')

    collection = db.get_collection('schedule')
    cursor = collection.find({'docker.network': {'$exists': 1}})[:]

    for document in cursor:
        del document['docker']['network']

        document['docker']['volume'] = '/data/nlp_home/docker/crawler:/crawler:ro'

        str_document = json.dumps(document, indent=4, ensure_ascii=False, sort_keys=True)
        print(str_document, flush=True)

        # collection.replace_one({'_id': document['_id']}, document, upsert=True)

    cursor.close()

    connect.close()

    return


if __name__ == '__main__':
    # change_volume()
    change_db_info()
    # change_network()
