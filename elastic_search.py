#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import json
import logging
import urllib3

from datetime import datetime
from dateutil.parser import parse as parse_date
from elasticsearch import Elasticsearch

# SSL 워닝 제거
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class NCElasticSearch:
    """
    엘라스틱 서치
    """
    def __init__(self, host=None, index_name=None):
        """
        엘라스틱 서치 생성자

        :param host: 엘라스틱 서치 서버명
        :param index_name: 인덱스
        """
        self.host = host
        self.index_name = index_name

        self.elastic_search = None
        if host is not None:
            self.open(self.host)

    def open(self, host=None, index_name=None, auth=True):
        """
        엘라스틱 서치 오픈

        :param host:
        :param index_name:
        :param auth:
        :return:
        """
        if host is not None:
            self.host = host

        if index_name is not None:
            self.index_name = index_name

        print('host:', self.host, flush=True)
        if auth is True:
            self.elastic_search = Elasticsearch(
                [self.host],
                http_auth=('elastic', 'nlplab'),
                use_ssl=True,
                verify_certs=False,
                port=9200)
        else:
            self.elastic_search = Elasticsearch(
                [self.host],
                use_ssl=True,
                verify_certs=False,
                port=9200)

        return self.elastic_search

    def create_index(self, index_name=None):
        """
        인덱스 생성

        :param index_name:
        :return:
        """
        if index_name is not None:
            self.index_name = index_name

        if self.elastic_search is None:
            return

        entry_settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }

        print("creating '%s' index..." % index_name, flush=True)
        result = self.elastic_search.indices.create(index=index_name, body={"settings": entry_settings})
        print(" response: ", result, flush=True)

        return result

    @staticmethod
    def copy_value(source, target):
        """
        문장 버퍼링을 위해 값을 복사

        :param source:
        :param target:
        :return:
        """
        for k in source:
            if k == 'date':
                if isinstance(source[k], datetime.date) is True:
                    dt = source[k]
                else:
                    dt = parse_date(source[k])

                target[k] = dt.strftime('%Y-%m-%dT%H:%M:%S')
            else:
                target[k] = source[k]

        return target

    def delete_index(self, index_name=None):
        """
        인덱스 삭제

        :param index_name:
        :return:
        """
        if self.elastic_search is None:
            return

        if index_name is not None:
            self.index_name = index_name

        print("deleting '{}' index...".format(self.index_name), flush=True)
        res = self.elastic_search.indices.delete(index=self.index_name)
        print(" response: '%s'" % res, flush=True)

        return

    def delete_type(self, index_name=None, type_name=None):
        """
        타입 삭제

        :param index_name:
        :param type_name:
        :return:
        """
        if self.elastic_search is None:
            return

        if index_name is not None:
            self.index_name = index_name

        count = self.elastic_search.count(index_name, type_name)['count']

        limit = 1000
        while count > 0:
            if limit < 0:
                break
            limit -= 1

            print('count: {:,}'.format(count), end='\r', file=sys.stderr, flush=True)
            response = self.elastic_search.search(
                index=index_name,
                filter_path=["hits.hits._id"],
                body={
                    "size": 1000,
                    "query": {
                        "filtered": {
                            "filter": {
                                "type": {
                                    "value": type_name
                                }
                            }
                        }
                    }
                }
            )

            bulk_data = [
                '{{"delete": {{"_index": "{}", "_type": "{}", "_id": "{}"}}}}'.format(
                    index_name, type_name, x["_id"]
                ) for x in response["hits"]["hits"]]

            self.elastic_search.bulk(index=index_name, doc_type=type_name, body=bulk_data, refresh=True)

            count = self.elastic_search.count(index_name, type_name)['count']

        return

    def find_one(self, index_name=None, type_name=None):
        """
        검색

        :param index_name:
        :param type_name:
        :return:
        """
        if self.elastic_search is None:
            return

        if index_name is not None:
            self.index_name = index_name

        count = self.elastic_search.count(index_name, type_name)['count']
        print(count)

        response = self.elastic_search.search(
            index=index_name,
            filter_path=["hits.hits._id"],
            body={
                "size": 1,
                "query": {
                    "filtered": {
                        "filter": {
                            "type": {
                                "value": type_name
                            }
                        }
                    }
                }
            }
        )

        print(response)

        return

    def search(self, keyword, index_name=None):
        """
        검색

        :param keyword:
        :param index_name:
        :return:
        """
        if index_name is not None:
            self.index_name = index_name

        print("searching...")
        search_result = self.elastic_search.search(index=self.index_name, size=10, body={
            'from': 1,
            'size': 100,
            "query": {
                'match': {
                    'keyword': {
                        'query': keyword,
                        'operator': 'and'
                    }
                }
            }
        })

        print(" response: '%s'" % search_result)

        print("results:")
        for hit in search_result['hits']['hits']:
            print(hit["_source"])

        return

    def insert_documents(self, index_name, type_name=None):
        """
        문서 입력

        :param index_name:
        :param type_name:
        :return:
        """
        # if self.elastic_search.indices.exists(index_name) is False:
        #     self.create_index(index_name)

        count = 0
        bulk_data = []
        for line in sys.stdin:
            line = line.strip()

            if line == '':
                continue

            document = json.loads(line)

            document['document_id'] = document['_id']
            del document['_id']

            # 날짜 변환, mongodb 의 경우 날짜가 $date 안에 들어가 있음.
            for k in document:
                try:
                    if '$date' in document[k]:
                        document[k] = document[k]['$date']
                except Exception as e:
                    logging.error('', exc_info=e)

                    print(document['document_id'], document[k], flush=True)

            # 인덱스의 타입을 지정하지 않았을 경우 날짜로 저장함
            index_type = type_name
            if type_name is None:
                if 'date' in document:
                    if isinstance(document['date'], datetime) is True:
                        dt = document['date']
                    else:
                        dt = parse_date(document['date'])

                    index_type = dt.strftime('%Y-%m')

            if index_type is None:
                print('ERROR (type extraction): ', document['date'], document['document_id'], flush=True)
                continue

            # elasticsearch 에서 날짜 인식 형식인 2017-10-10T12:00:00 으로 변환
            if document['date'][-1] == 'Z':
                document['date'] = document['date'][0:len(document['date'])-1]

            bulk_data.append({
                "update": {
                    "_index": index_name,
                    "_type": index_type,
                    "_id": document['document_id']
                }
            })
            bulk_data.append({
                "doc": document,
                "doc_as_upsert": True
            })

            count += 1

            if len(bulk_data) > 1000:
                print('{:,}\t{}\t{}'.format(count, index_name, index_type), flush=True)
                self.elastic_search.bulk(index=index_name, body=bulk_data, refresh=True, request_timeout=120)
                bulk_data = []

        if len(bulk_data) > 0:
            print('{:,}'.format(count), flush=True)
            self.elastic_search.bulk(index=index_name, body=bulk_data, refresh=True, request_timeout=120)

    @staticmethod
    def parse_argument():
        """
        파라메터 옵션 정의

        :return:
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='')

        arg_parser.add_argument('-host', help='서버 이름', default='frodo')

        arg_parser.add_argument('-index', help='인덱스', default='baseball')
        arg_parser.add_argument('-type', help='타입', default=None)

        arg_parser.add_argument('-insert', help='문서 입력', action='store_true', default=False)

        return arg_parser.parse_args()


if __name__ == "__main__":
    self = NCElasticSearch()

    args = self.parse_argument()
    self.open(args.host, args.index)

    if args.insert is True:
        self.insert_documents(index_name=args.index, type_name=args.type)
