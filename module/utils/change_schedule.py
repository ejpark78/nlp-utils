#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from pymongo import MongoClient


def open_db(db_name, host='frodo', port=27018):
    """ 몽고 디비 핸들 오픈 """
    connect = MongoClient('mongodb://{}:{}'.format(host, port))
    db = connect.get_database(db_name)

    return connect, db


def change_db_info():
    """ 크롤링 스케쥴 정보 변경 """
    from datetime import datetime

    connect, db = open_db('crawler')

    collection = db.get_collection('schedule_list')

    cursor = collection.find({})[:]

    date = datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
    fp = open('backup-{}.json'.format(date), 'a')

    for document in cursor:
        # 백업
        str_document = json.dumps(document, indent=4, ensure_ascii=False, sort_keys=True)
        fp.write(str_document + '\n\n')

        document_id = document['_id']
        print(document_id, flush=True)

        if 'docker' not in document:
            continue

        docker = document['docker']

        docker['image'] = 'nlpapi:5000/crawler:1.0'

        # if 'parameter' not in document:
        #     continue
        #
        # parameter = document['parameter']
        #
        # if 'db_info' not in parameter:
        #     continue
        #
        # db_info = parameter['db_info']

        # if 'elastic' in db_info:
        #     elastic = db_info['elastic']
        #     elastic['host'] = 'http://frodo01:9200'
        #
        # if 'article_list' in db_info:
        #     elastic = db_info['article_list']
        #     elastic['host'] = 'http://frodo01:9200'

        # if 'corpus-process' in db_info:
        #     elastic = db_info['corpus-process']
        #     elastic['host'] = 'http://nlp.ncsoft.com:10009/v1.0/batch'

        # schedule = document['schedule']
        # if 'sleep_range' in schedule:
        #     schedule['sleep_range'] = '03,05'

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
