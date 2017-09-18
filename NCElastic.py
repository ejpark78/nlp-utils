#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(UserWarning)


class NCElastic:
    def __init__(self, es_host=None, index_name=None):
        self.es_host = es_host
        self.index_name = index_name

        self.elastic_search = None
        if es_host is not None:
            self.open(self.es_host)

    def open(self, es_host=None, index_name=None, auth=True):
        """
        엘라스틱 서치 생섣
        """
        if es_host is not None:
            self.es_host = es_host

        if index_name is not None:
            self.index_name = index_name

        from elasticsearch import Elasticsearch

        print('es_host:', self.es_host, flush=True)
        if auth is True:
            self.elastic_search = Elasticsearch(
                [self.es_host],
                http_auth=('elastic', 'nlplab'),
                use_ssl=True,
                verify_certs=False,
                port=9200)
        else:
            self.elastic_search = Elasticsearch(
                [self.es_host],
                use_ssl=True,
                verify_certs=False,
                port=9200)

        return self.elastic_search

    def create_index(self, index_name=None):
        """
        인덱스 생성
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
        """
        import dateutil.parser
        from datetime import datetime

        for k in source:
            if k == 'date':
                if isinstance(source[k], datetime.date) is True:
                    dt = source[k]
                else:
                    dt = dateutil.parser.parse(source[k])

                target[k] = dt.strftime('%Y-%m-%dT%H:%M:%S')
            else:
                target[k] = source[k]

        return target

    def delete_index(self, index_name=None):
        """
        인덱스 삭제
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
        타입 삭제
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

    def insert_documents(self, es_host, index_name, type_name):
        """
        인덱스 생성
        """
        import json

        import urllib3
        urllib3.disable_warnings()

        self.open(es_host=es_host, index_name=index_name)

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
                except Exception as err:
                    print(document['document_id'], flush=True)

            if document['date'][-1] == 'Z':
                document['date'] = document['date'][0:len(document['date'])-1]
                # print(document['date'], flush=True)

            bulk_data.append({
                "update": {
                    "_index": index_name,
                    "_type": type_name,
                    "_id": document['document_id']
                }
            })
            bulk_data.append({
                "doc": document,
                "doc_as_upsert": True
            })

            count += 1

            if len(bulk_data) > 1000:
                print('{:,}\t{}\t{}'.format(count, index_name, type_name), flush=True)
                self.elastic_search.bulk(index=index_name, body=bulk_data, refresh=True, request_timeout=120)
                bulk_data = []

        if len(bulk_data) > 0:
            print('{:,}'.format(count), flush=True)
            self.elastic_search.bulk(index=index_name, body=bulk_data, refresh=True, request_timeout=120)

    @staticmethod
    def parse_argument():
        """
        파라메터 옵션 정의
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='')

        arg_parser.add_argument('-index', help='index name', default='baseball')
        # arg_parser.add_argument('-es_host', help='elastic search host name', default='https://elastic:changeme@gollum.ncsoft.com')
        arg_parser.add_argument('-es_host', help='elastic search host name', default='frodo')
        arg_parser.add_argument('-type', help='type name', default='2016')

        arg_parser.add_argument('-search', help='search', action='store_true', default=False)
        arg_parser.add_argument('-keyword', help='keyword', default=None)

        arg_parser.add_argument('-limit', help='limit', type=int, default=-1)

        arg_parser.add_argument('-create_index', help='create index', action='store_true', default=False)
        arg_parser.add_argument('-delete_index', help='delete index', action='store_true', default=False)
        arg_parser.add_argument('-delete_type', help='delete type', action='store_true', default=False)
        arg_parser.add_argument('-insert_documents', help='insert documents', action='store_true', default=False)

        return arg_parser.parse_args()


if __name__ == "__main__":
    self = NCElastic()

    args = self.parse_argument()
    self.open(args.es_host, args.index)

    if args.search is True:
        self.search(args.keyword, index_name=args.index_name)
    elif args.create_index is True:
        self.create_index(args.index_name)
    elif args.delete_index is True:
        self.delete_index(args.index_name)
    elif args.delete_type is True:
        self.delete_type(args.index_name, args.type_name)
    elif args.insert_documents is True:
        self.insert_documents(es_host=args.es_host, index_name=args.index, type_name=args.type)
    else:
        self.find_one(args.index_name, args.type_name)
