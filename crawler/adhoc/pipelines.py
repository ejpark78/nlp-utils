# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import ssl
from base64 import decodebytes
from os import getenv
from ssl import SSLContext

import urllib3
# useful for handling different item types with a single interface
from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


class AdhocPipeline:

    def __init__(self):
        self.host = getenv('ELASTIC_SEARCH_HOST', default='https://corpus.ncsoft.com:9200')
        self.http_auth = getenv('ELASTIC_SEARCH_AUTH', default='ZWxhc3RpYzpubHBsYWI=')

        self.es = Elasticsearch(
            hosts=self.host,
            http_auth=decodebytes(self.http_auth.encode('utf-8')).decode('utf-8'),
            verify_certs=False,
            ssl_show_warn=False,
            ssl_context=self.get_ssl_verify_mode(),
            http_compress=True,
        )

        self.mapping = {
            'settings': {
                'number_of_shards': 1,
                'number_of_replicas': 1
            },
            'mappings': {
                'properties': {
                    'url': {
                        'type': 'keyword'
                    },
                    'title': {
                        'type': 'text'
                    },
                    'date': {
                        'type': 'date'
                    },
                    'contents': {
                        'type': 'text'
                    },
                    'raw': {
                        'enabled': False
                    },
                    'raw_list': {
                        'enabled': False
                    },
                    '@list_crawl_date': {
                        'type': 'date'
                    }
                }
            }
        }

    @staticmethod
    def get_ssl_verify_mode() -> SSLContext:
        ssl_context = create_ssl_context()

        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        return ssl_context

    def create_index(self, es: Elasticsearch, index: str) -> bool:
        """인덱스를 생성한다."""
        if es is None or es.indices.exists(index=index) is True:
            return False

        try:
            es.indices.create(index=index, body=self.mapping)
        except Exception as e:
            return False

        return True

    def process_item(self, item: dict, spider):
        index, doc_id = item['_index'], item['_id']

        del item['_index']
        del item['_id']

        self.create_index(es=self.es, index=index)

        bulk = [{
            'update': {
                '_id': doc_id,
                '_index': index,
            }
        }, {
            'doc': item,
            'doc_as_upsert': True,
        }]

        resp = self.es.bulk(index=index, body=bulk, refresh=True)

        return item
