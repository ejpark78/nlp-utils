#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import requests
import urllib3
from pymongo import MongoClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


def send_document_list(url, db_name, doc_type, document_list, update):
    """

    :param url:
    :param db_name:
    :param doc_type:
    :param document_list:
    :param update:
    :return:
    """

    if len(document_list) == 0:
        return

    body = {
        'index': db_name,
        'doc_type': doc_type,
        'document_id': document_list,
        'update': update
    }

    headers = {'Content-Type': 'application/json'}
    result = requests.post(url=url, json=body, headers=headers,
                           allow_redirects=True, timeout=5, verify=False)

    print('result: ', result, flush=True)

    return


def change_db_info():
    """
    :return:
    """
    host = 'frodo'
    port = 27018

    url = 'http://localhost:5004/v1.0/api/batch'
    # url = 'https://gollum02:5004/v1.0/api/batch'

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
        'chosun_sports'
    ]

    update = True

    count = 0
    for db_name in db_list:
        db = connect.get_database(db_name)

        for i in range(1, 4):
            doc_type = '2018-{:02d}'.format(i)

            collection = db.get_collection(doc_type)
            cursor = collection.find({}, {'_id': 1})[:]

            document_list = []
            for document in cursor:
                count += 1
                document_id = document['_id']
                print(db_name, doc_type, document_id, flush=True)

                document_list.append(document_id)

                if len(document_list) > 100:
                    send_document_list(url=url, db_name=db_name, doc_type=doc_type,
                                       document_list=document_list, update=update)
                    document_list = []

            if len(document_list) > 0:
                send_document_list(url=url, db_name=db_name, doc_type=doc_type,
                                   document_list=document_list, update=update)

            cursor.close()
            print('')

    connect.close()

    print('count: {:,}'.format(count), flush=True)

    return


def save_s3(document, s3_info, db_name):
    """
    S3에 기사 이미지 저장

    :param document: 저장할 문서
    :param s3_info:
        {
            bucket: 'bucket name',
            url: 'http://paige-cdn.plaync.com'
        }
    :param db_name: 디비명
    :return: document
    """
    import os
    import logging

    # 이미지 목록 추출
    image_list = None
    if 'image_list' in document:
        image_list = document['image_list']

    # 추출된 이미지 목록이 없을 경우
    if image_list is None:
        return

    import boto3
    import pathlib

    # http://boto3.readthedocs.io/en/latest/reference/services/s3.html
    bucket_name = s3_info['bucket']
    aws_access_key_id = os.getenv('S3_ACCESS_KEY', 'AKIAI5X5SF6WJK3SFXDA')
    aws_secret_access_key = os.getenv('S3_SECRET_ACCESS_KEY', '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')

    s3 = boto3.resource('s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key)

    bucket = s3.Bucket(bucket_name)

    # 이미지 목록
    count = 0
    prefix = document['document_id']
    for image in image_list:
        url = image['image']

        # 이미지 확장자 추출
        suffix = pathlib.Path(url).suffix

        # 1. 이미지 파일 다운로드
        r = requests.get(url)

        upload_file = '{}/{}-{:02d}{}'.format(db_name, prefix, count, suffix)
        count += 1

        # 2. s3에 업로드
        try:
            response = bucket.put_object(Key=upload_file, Body=r.content, ACL='public-read',
                                         ContentType=r.headers['content-type'])
            logging.info(msg='save S3: {}'.format(response))

            # cdn 이미지 주소 추가
            image['cdn_image'] = '{}/{}'.format(s3_info['url_prefix'], upload_file)
        except Exception as e:
            logging.error(msg='s3 저장 오류: {}'.format(e))

    # 이미지 목록 업데이트
    document['image_list'] = image_list

    return document


def convert_date(document):
    """
    날짜 형식을 elastic search 에서 검색할 수 있도록 변경

    :param document:
    :return:
    """
    from datetime import datetime
    from dateutil.parser import parse as parse_date

    # 날짜 변환
    if 'date' in document:
        if isinstance(document['date'], str):
            document['date'] = parse_date(document['date'])

        document['date'] = document['date'].strftime('%Y-%m-%dT%H:%M:%S')

    # 입력시간 삽입
    if 'insert_date' not in document:
        document['insert_date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    return document


def save_elastic(document, index, doc_type, host):
    """
    elastic search 에 저장

    :param document: 문서
    :param index: 문서
    :param doc_type: 문서
    :param host: 문서
    :return: None
    """
    import logging

    from elasticsearch import Elasticsearch

    document = convert_date(document=document)

    try:
        elastic = Elasticsearch(host, timeout=5)

        if '_id' in document:
            document['document_id'] = document['_id']
            del document['_id']

        bulk_data = list()
        bulk_data.append({
            'update': {
                '_index': index,
                '_type': doc_type,
                '_id': document['document_id']
            }
        })

        bulk_data.append({
            'doc': document,
            'doc_as_upsert': True
        })

        ret = elastic.bulk(index=index, body=bulk_data, refresh=True)
        print(ret, flush=True)
    except Exception as e:
        logging.error(msg='elastic search 저장 오류: {}'.format(e))

    return


def download_image():
    """
    :return:
    """
    from elasticsearch import Elasticsearch

    index_name = 'yonhapnews_sports'
    host = 'http://nlpapi.ncsoft.com:9200'

    s3_info = {
        'bucket': 'paige-cdn-origin',
        'url_prefix': 'http://paige-cdn.plaync.com'
    }

    elastic = Elasticsearch(host)

    start = 0
    size = 100
    total = 100000

    max_try = 100

    while start < total:
        max_try -= 1
        if max_try < 0:
            break

        query_body = {
            'from': start,
            'size': start + size
        }

        search_result = elastic.search(index=index_name, body=query_body)

        hits = search_result['hits']
        total = hits['total']

        print('start: ', start, ', total:', total, flush=True)

        start += size

        for item in hits['hits']:
            document = item['_source']

            save_flag = False
            if 'insert_date' not in document:
                save_flag = True
                document['insert_date'] = document['date']

            if document['date'] != document['insert_date']:
                document['insert_date'] = document['date']

            # print(document['date'], document['insert_date'], flush=True)

            image_list = document['image_list']
            if len(image_list) > 0:
                for image in image_list:
                    if 'image' in image and 'cdn_image' not in image:
                        save_flag = True

                        # 이미지 다운로드
                        document = save_s3(document, s3_info, index_name)

            if save_flag is True:
                # 저장
                save_elastic(document, item['_index'], item['_type'], host)
                print(document, flush=True)

    return


if __name__ == '__main__':
    # change_db_info()
    download_image()
