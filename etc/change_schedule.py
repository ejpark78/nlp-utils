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
    connect, db = open_db('crawler')

    collection = db.get_collection('schedule')
    # cursor = collection.find({'group': 'naver_crawler'})[:]
    # cursor = collection.find({'_id': {'$regex': 'image'}})[:]
    # cursor = collection.find({'_id': 'crawler_nate_economy_2017'})[:]
    # cursor = collection.find({'parameter.db_info.mongo.host': 'frodo01'})[:]
    # cursor = collection.find({'docker.network': 'hadoop-net'})[:]

    cursor = collection.find({'_id': {'$regex': 'lineagem'}})[:]

    for document in cursor:
        print(document['_id'], flush=True)

        if 'delay' in document:
            del document['delay']

        if 'min_delay' in document['parameter']:
            del document['parameter']['min_delay']

        document['parameter']['delay'] = '10~15'

        document['docker'] = {
            'image': 'crawler:dev',
            'command': '.venv/bin/python3 scheduler.py',
            'volume': '/data/nlp_home/docker/crawler:/data/nlp_home/docker/crawler:ro',
            'working_dir': '/data/nlp_home/docker/crawler'
        }

        document['sleep_range'] = '01,02,03,04,05,06'

        str_document = json.dumps(document, indent=4, ensure_ascii=False, sort_keys=True)
        print(str_document, flush=True)

        # collection.replace_one({'_id': document['_id']}, document, upsert=True)

    cursor.close()

    connect.close()

    return


if __name__ == '__main__':
    change_db_info()
