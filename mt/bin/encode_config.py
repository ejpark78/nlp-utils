#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

import jwt
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)

logger = logging.getLogger()


class EncodeConfig(object):
    """ """

    def __init__(self):
        """ 생성자 """

    @staticmethod
    def get_export_config():
        """ """
        payload = {
            "host": "https://corpus.ncsoft.com:9200",
            "auth": "elastic:nlplab",
            "index": "corpus-bitext",
            "limit": 0,
            "query": {
                "_source": ["korean_token", "english_token"],
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "source": {
                                        "query": "aihub",
                                        "zero_terms_query": "all"
                                    }
                                }
                            },
                            {
                                "bool": {
                                    "should": [
                                        {
                                            "match": {
                                                "style": {
                                                    "query": "대화체",
                                                    "zero_terms_query": "none"
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }

        jwt_str = jwt.encode(payload, '').decode('utf-8')
        print(jwt_str)

        return jwt.decode(jwt_str)

    @staticmethod
    def get_upload_config():
        """ """
        payload = {
            'host': 'https://mt_pipeline:nlplab2020@corpus.ncsoft.com:8080',
            'local_path': 'model',
            'remote_path': '/mt_pipeline/moses/aihub-dialog-test',
            # 'remote_path': '/mt_pipeline/open-nmt/aihub-dialog',
        }

        jwt_str = jwt.encode(payload, '').decode('utf-8')
        print(jwt_str)

        return jwt.decode(jwt_str)

    @staticmethod
    def parse_lucene_query(query):
        """ """
        from luqum.parser import parser
        from luqum.elasticsearch import ElasticsearchQueryBuilder

        tree = parser.parse(query)

        es_builder = ElasticsearchQueryBuilder(not_analyzed_fields=['published', 'tag'])

        return es_builder(tree)

    def batch(self):
        """ """

        # parse_lucene_query('source: aihub AND (style: 구어체 OR style: 대화체)')

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('--export', action='store_true', default=False, help='')
        parser.add_argument('--config', default=None)

        return parser.parse_args()


if __name__ == '__main__':
    EncodeConfig().batch()
