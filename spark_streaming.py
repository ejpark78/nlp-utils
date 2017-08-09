#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import json

from pyspark import SparkContext, SparkConf, storagelevel
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(UserWarning)


def create_elastic_index(elastic, index_name=None):
    """
    인덱스 생성
    """
    if elastic is None:
        return

    elastic.indices.create(
        index=index_name,
        body={
            'settings': {
                'number_of_shards': 1,
                'number_of_replicas': 0
            }
        }
    )

    return


def save_elastic(document, host, index, type, auth=('elastic', 'nlplab')):
    """
    elastic search에 저장
    """
    # 날짜 변환
    if 'date' in document:
        document['date'] = document['date'].strftime('%Y-%m-%dT%H:%M:%S')

    # 입력시간 삽입
    from datetime import datetime
    document['insert_date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    try:
        from elasticsearch import Elasticsearch

        if auth is True:
            elastic = Elasticsearch(
                [host],
                http_auth=('elastic', 'nlplab'),
                use_ssl=True,
                verify_certs=False,
                port=9200)
        else:
            elastic = Elasticsearch(
                [host],
                use_ssl=True,
                verify_certs=False,
                port=9200)

        if elastic.indices.exists(index) is False:
            create_elastic_index(elastic, index)

        document['document_id'] = document['_id']
        del document['_id']

        bulk_data = []
        bulk_data.append({
            'update': {
                '_index': index,
                '_type': type,
                '_id': document['document_id']
            }
        })

        bulk_data.append({
            'doc': document,
            'doc_as_upsert': True
        })

        elastic.bulk(index=index, body=bulk_data, refresh=True)

    except Exception:
        print('ERROR at save elastic: {}'.format(sys.exc_info()[0]))

    return


def save_mongodb(document, host, db_name, collection, port):
    """
    몽고 디비에 저장
    """
    try:
        from datetime import datetime
        from pymongo import MongoClient

        connect = MongoClient('mongodb://{}:{}'.format(host, port))

        document['insert_date'] = datetime.now()

        result_db = connect[db_name]
        result_db[collection].replace_one({'_id': document['_id']}, document, upsert=True)

        connect.close()
    except Exception:
        print('ERROR at save mongodb: {}'.format(sys.exc_info()[0]))

    return


def map_function(x):
    """
    개별 excutor 에서 실행되는 작업
    """
    manager = global_manager.value

    # 형태소 및 개체명 인식기 사전 오픈
    line = x[1].strip()

    line = line.strip()
    if line == '':
        return ''

    try:
        document = json.loads(line)
    except Exception:
        msg = 'ERROR at json parsing: {}'.format(line)
        return msg

    host = '172.20.78.159' # 'gollum02'
    domain = manager.util.domain
    db_name = 'spark_streaming'
    collection = 'crawler'
    port = 27017

    # 크롤러 메타 정보 제거
    if 'crawler_meta' in document:
        domain = document['crawler_meta']['domain']
        db_name = document['crawler_meta']['name']
        collection = document['crawler_meta']['collection']

        del document['crawler_meta']

    # 사전 오픈
    try:
        manager.util.open_pos_tagger()
        manager.util.open_sp_project_ner(domain=domain)
    except Exception:
        return 'ERROR at open pos tagger: {}'.format(sys.exc_info()[0])

    # 전처리 실행
    try:
        result = manager.spark_batch(document)

        if 'ERROR' in result:
            return result['ERROR']
    except Exception:
        return 'ERROR at run spark_batch: {}'.format(sys.exc_info()[0])

    # 분석 결과 저장
    try:
        if 'content' in result:
            # 날짜 변환
            if 'date' in result:
                if '$date' in result['date']:
                    result['date'] = result['date']['$date']

                import dateutil.parser
                result['date'] = dateutil.parser.parse(result['date'])

            save_mongodb(result.copy(), host=host, db_name=db_name, collection=collection, port=port)
            save_elastic(result.copy(), host='gollum', index=db_name, type=collection, auth=None)
            save_elastic(result.copy(), host='yoma07', index=db_name, type=collection, auth=('elastic', 'nlplab'))
    except Exception:
        return 'ERROR at save: {}'.format(sys.exc_info()[0])

    msg = 'OK'
    try:
        buf = [db_name, collection]
        for k in ['date', '_id', 'title']:
            if k in result:
                buf.append('{}'.format(result[k]))

        msg = '\t'.join(buf)
    except Exception:
        return 'ERROR at log msg'

    return msg


def update_library(sc):
    """
    """
    sc.addFile('hdfs:///user/root/src/_NCKmat.so')
    sc.addFile('hdfs:///user/root/src/_NCSPProject.so')
    sc.addFile('hdfs:///user/root/src/sp_config.ini')

    sc.addPyFile('hdfs:///user/root/src/NCKmat.py')
    sc.addPyFile('hdfs:///user/root/src/NCSPProject.py')
    sc.addPyFile('hdfs:///user/root/src/NCPreProcess.py')
    sc.addPyFile('hdfs:///user/root/src/NCCrawlerUtil.py')
    sc.addPyFile('hdfs:///user/root/src/NCNlpUtil.py')
    sc.addPyFile('hdfs:///user/root/src/NCHtmlParser.py')
    sc.addPyFile('hdfs:///user/root/src/NCNewsKeywords.py')

    return


def parse_argument():
    """"
    옵션 입력
    """
    import argparse

    arg_parser = argparse.ArgumentParser(description='')

    arg_parser.add_argument('-host', help='mongodb host name', default='172.20.78.159') # gollum02
    arg_parser.add_argument('-port', help='mongodb host port', default=27017)
    arg_parser.add_argument('-db_name', help='mongodb name', default='spark_streaming')

    arg_parser.add_argument('-domain', help='domain', default='economy')

    arg_parser.add_argument('-topic', help='kafka topic', default='crawler')

    arg_parser.add_argument('-debug', help='debug', action='store_true', default=False)

    return arg_parser.parse_args()


if __name__ == "__main__":
    conf = SparkConf()
    sc = SparkContext(appName='crawler', conf=conf)

    update_library(sc)

    args = parse_argument()

    # 사전 초기화
    from NCNlpUtil import NCNlpUtil
    from NCPreProcess import NCPreProcess
    from NCHtmlParser import NCHtmlParser
    from NCNewsKeywords import NCNewsKeywords

    manager = NCPreProcess()
    manager.util = NCNlpUtil()
    manager.parser = NCHtmlParser()

    # manager.util.open_pos_tagger()
    # manager.util.open_sp_project_ner(domain=domain)

    manager.util.domain = args.domain

    manager.keywords_extractor = NCNewsKeywords(entity_file_name='dictionary/keywords/nc_entity.txt')

    global_manager = sc.broadcast(manager)

    ssc = StreamingContext(sc, 3)

    ds = KafkaUtils.createDirectStream(ssc, [args.topic], {'metadata.broker.list': 'master:9092'})

    result = ds.map(map_function)
    result.pprint()

    # db_info = {
    #     'host': args.host,
    #     'port': args.port,
    #     'db_name': args.db_name,
    #     'collection': args.topic
    # }
    #
    # # 결과 저장
    # result.foreachRDD(lambda rdd: rdd.foreach(lambda x: save_result(x, db_info)))

    ssc.start()
    ssc.awaitTermination()

    global_manager.unpersist()
    global_manager.destroy()
