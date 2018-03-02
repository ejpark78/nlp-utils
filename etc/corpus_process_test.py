#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import requests
from pymongo import MongoClient


def send_document_list(url, db_name, doc_type, document_list):
    """

    :param url:
    :param db_name:
    :param doc_type:
    :param document_list:
    :return:
    """

    if len(document_list) == 0:
        return

    body = {
        'index': db_name,
        'doc_type': doc_type,
        'document_id': document_list,
        'update': False
    }

    headers = {'Content-Type': 'application/json'}
    result = requests.put(url=url, json=body, headers=headers,
                          allow_redirects=True, timeout=5, verify=False)

    print('result: ', result, flush=True)

    return


def change_db_info():
    """
    :return:
    """
    host = 'frodo'
    port = 27018

    # url = 'http://localhost:5004/v1.0/api/batch'
    url = 'https://gollum02:5004/v1.0/api/batch'

    connect = MongoClient('mongodb://{}:{}'.format(host, port))

    # db_list = connect.list_database_names()

    # 'daum_3min_baseball', 'daum_baseball_game_info', 'daum_culture', 'daum_economy', 'daum_editorial',
    # 'daum_international', 'daum_it', 'daum_politics', 'daum_society', 'daum_sports',

    # 'nate_economy', 'nate_entertainment', 'nate_international', 'nate_it', 'nate_opinion', 'nate_photo',
    # 'nate_politics', 'nate_radio', 'nate_society', 'nate_sports', 'nate_tv',

    # 'jisikman_app',
    # 'lineagem_free', 'mlbpark_kbo',

    # 'naver_economy', 'naver_international', 'naver_it', 'naver_kin_baseball', 'naver_living',
    # 'naver_opinion', 'naver_politics', 'naver_society', 'naver_sports', 'naver_tv',

    # 'chosun_sports', 'donga_baseball', 'einfomax_finance', 'joins_baseball', 'joins_live_baseball',
    # 'khan_baseball', 'mk_sports', 'monoytoday_sports', 'newsis_sports', 'osen_sports', 'sportschosun_baseball',
    # 'sportskhan_baseball', 'spotv_baseball', 'starnews_sports', 'yonhapnews_sports', 'yonhapnewstv_sports'

    db_list = [
        'daum_economy',
        # 'nate_economy',
        # 'naver_economy'
    ]

    count = 0
    for db_name in db_list:
        db = connect.get_database(db_name)

        for i in range(1, 13):
            doc_type = '2017-{:02d}'.format(i)

            collection = db.get_collection(doc_type)
            cursor = collection.find({}, {'_id': 1})[:]

            document_list = []
            for document in cursor:
                count += 1
                document_id = document['_id']
                print(db_name, doc_type, document_id, flush=True)

                document_list.append(document_id)

                if len(document_list) > 100:
                    send_document_list(url=url, db_name=db_name, doc_type=doc_type, document_list=document_list)
                    document_list = []

            if len(document_list) > 0:
                send_document_list(url=url, db_name=db_name, doc_type=doc_type, document_list=document_list)

            cursor.close()

    connect.close()

    print('count: {:,}'.format(count), flush=True)

    return


if __name__ == '__main__':
    change_db_info()
