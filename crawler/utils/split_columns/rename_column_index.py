#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from crawler.utils.elasticsearch import ElasticSearchUtils


class RenameColumnName(object):

    def __init__(self):
        super().__init__()

        self.elastic_info = {
            'host': 'https://corpus.ncsoft.com:9200',
            'http_auth': 'elastic:nlplab'
        }

    def batch(self) -> None:
        es = ElasticSearchUtils(**self.elastic_info)

        index = 'crawler-naver-economy-2021'

        query = {
            'track_total_hits': True,
            '_source': ['title', 'date', 'url', 'raw', 'html', 'content'],
            "query": {
                "bool": {
                    "must_not": {
                        "exists": {
                            "field": "content"
                        }
                    }
                }
            }
        }

        resp = es.conn.search(index=index, body=query)

        if 'hits' in resp and 'hits' in resp['hits']:
            hits = resp['hits']

            total = hits['total']['value']
            for item in hits['hits']:
                doc = item['_source']

        return


if __name__ == '__main__':
    RenameColumnName().batch()
