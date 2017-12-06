#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import json
import urllib3
import logging

from pyspark import SparkContext, SparkConf
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class SparkStreaming:
    """
    """

    def __init__(self):
        self.global_manager = None

    @staticmethod
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

    def save_elastic(self, document, result_info):
        """
        elastic search에 저장

        :param document:
        :param result_info:
        :return:
        """
        # 날짜 변환
        if 'date' in document:
            document['date'] = document['date'].strftime('%Y-%m-%dT%H:%M:%S')

        # 입력시간 삽입
        from datetime import datetime
        document['insert_date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        # defaults
        if 'port' not in result_info:
            result_info['port'] = 9200

        try:
            from elasticsearch import Elasticsearch

            elastic = Elasticsearch(
                [result_info['host']],
                http_auth=('elastic', 'nlplab'),
                use_ssl=True,
                verify_certs=False,
                port=result_info['port'])

            if elastic.indices.exists(result_info['index']) is False:
                self.create_elastic_index(elastic, result_info['index'])

            document['document_id'] = document['_id']
            del document['_id']

            bulk_data = list()
            bulk_data.append({
                'update': {
                    '_index': result_info['index'],
                    '_type': result_info['type'],
                    '_id': document['document_id']
                }
            })

            bulk_data.append({
                'doc': document,
                'doc_as_upsert': True
            })

            elastic.bulk(index=result_info['index'], body=bulk_data, refresh=True)
        except Exception as e:
            logging.error('', exc_info=e)

            print('ERROR at save elastic: {}'.format(sys.exc_info()[0]))

        return

    @staticmethod
    def save_mongodb(document, host, db_name, collection, port):
        """
        몽고 디비에 저장

        :param document:
        :param host:
        :param db_name:
        :param collection:
        :param port:
        :return:
        """
        try:
            from datetime import datetime
            from pymongo import MongoClient

            connect = MongoClient('mongodb://{}:{}'.format(host, port))

            document['insert_date'] = datetime.now()

            result_db = connect[db_name]
            result_db[collection].replace_one({'_id': document['_id']}, document, upsert=True)

            connect.close()

        except Exception as e:
            logging.error('', exc_info=e)

            print('ERROR at save mongodb: {}'.format(sys.exc_info()[0]))

        return

    def map_function(self, x):
        """
        개별 excutor 에서 실행되는 작업

        :param x:
        :return:
        """
        manager = self.global_manager.value

        # 형태소 및 개체명 인식기 사전 오픈
        line = x[1].strip()

        line = line.strip()
        if line == '':
            return ''

        try:
            document = json.loads(line)

        except Exception as e:
            logging.error('', exc_info=e)

            return 'ERROR at json parsing: {}'.format(line)

        # 크롤러 메타 정보 제거
        result_info = {}
        if 'crawler_meta' in document:
            if 'result' in document['crawler_meta']:
                result_info = document['crawler_meta']['result'].copy()

            del document['crawler_meta']

        # 사전 오픈
        try:
            manager.util.open_pos_tagger()
            manager.util.open_multi_domain_ner()
        except Exception as e:
            logging.error('', exc_info=e)
            return 'ERROR at open pos tagger: {}'.format(sys.exc_info()[0])

        # 전처리 실행
        try:
            result = manager.spark_batch(document)

            if 'ERROR' in result:
                return result['ERROR']
        except Exception as e:
            logging.error('', exc_info=e)
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

                if 'elastic' in result_info:
                    self.save_elastic(result.copy(), result_info=result_info['elastic'])
        except Exception as e:
            logging.error('', exc_info=e)
            return 'ERROR at save: {}'.format(sys.exc_info()[0])

        try:
            buf = [result_info['elastic']['index'], result_info['elastic']['type']]
            for k in ['date', '_id']:
                if k in result:
                    buf.append('{}'.format(result[k]))

            if isinstance(result['title'], str) is not True:
                buf.append('{}'.format(result['title']['sentence']))
            else:
                buf.append('{}'.format(result['title']))

            msg = '\t'.join(buf)
        except Exception as e:
            logging.error('', exc_info=e)
            return 'ERROR at log msg'

        return msg

    @staticmethod
    def update_library(sc, user_name='ejpark'):
        """
        :param sc:
        :param user_name:
        :return:
        """
        # for f_name in ('crawler/html_parser.py', 'crawler/utils.py',
        #                'language_utils/keyword_extractor.py', 'language_utils/language_utils.py',
        #                'language_utils/sp_utils/NCKmat.py', 'language_utils/sp_utils/NCSPProject.py'):
        #     sc.addPyFile('hdfs:///user/{}/libs/{}'.format(user_name, f_name))

        # for f_name in ('crawler.jar', 'language_utils.jar'):
        #     sc.addPyFile('hdfs:///user/{}/libs/{}'.format(user_name, f_name))

        for f_name in ('sp_config.ini',
                       'language_utils/sp_utils/_NCKmat.so', 'language_utils/sp_utils/_NCSPProject.so'):
            sc.addFile('hdfs:///user/{}/streaming/{}'.format(user_name, f_name))

        return


def init_arguments():
    """
    옵션 입력

    :return:
    """
    import argparse

    parser = argparse.ArgumentParser(description='')

    parser.add_argument('-host', help='mongodb host name', default='172.20.78.159')
    parser.add_argument('-port', help='mongodb host port', default=27017)
    parser.add_argument('-db_name', help='mongodb name', default='spark_streaming')

    parser.add_argument('-domain', help='domain', default='economy')

    parser.add_argument('-topic', help='kafka topic', default='crawler')

    parser.add_argument('-user_name', help='user name', default='ejpark')

    parser.add_argument('-debug', help='debug', action='store_true', default=False)

    return parser.parse_args()


def main():
    """

    :return:
    """

    manager = SparkStreaming()

    conf = SparkConf()
    sc = SparkContext(appName='crawler', conf=conf)

    args = init_arguments()

    manager.update_library(sc, user_name=args.user_name)

    # 사전 초기화
    from language_utils.language_utils import LanguageUtils

    language_utils = LanguageUtils()
    # keywords_extractor = KeywordExtractor(entity_file_name='dictionary/keywords/nc_entity.txt')

    manager.global_manager = sc.broadcast(language_utils)

    ssc = StreamingContext(sc, 3)

    ds = KafkaUtils.createDirectStream(ssc, [args.topic], {'metadata.broker.list': 'gollum:9092'})

    result = ds.map(manager.map_function)
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

    manager.global_manager.unpersist()
    manager.global_manager.destroy()

    return


if __name__ == "__main__":
    main()
