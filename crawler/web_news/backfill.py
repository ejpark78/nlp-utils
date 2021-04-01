#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import defaultdict

import pytz
from tqdm import tqdm

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.utils.logger import Logger


class Backfill(object):

    def __init__(self):
        self.params = None

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.es = {
            'corpus': ElasticSearchUtils(**{
                'host': 'https://corpus.ncsoft.com:9200',
                'http_auth': 'ZWxhc3RpYzpubHBsYWI=',
                'encoded_auth': True
            }),
            'backfill': ElasticSearchUtils(**{
                'host': 'https://crawler-es.cloud.ncsoft.com:9200',
                'http_auth': 'ZWxhc3RpYzpzZWFyY2hUMjAyMA==',
                'encoded_auth': True
            })
        }

    def dump(self, index: str, date_range: str) -> defaultdict(list):
        dt_query = self.es['backfill'].get_date_range_query(date_range=date_range)

        query = {
            'corpus': {
                'track_total_hits': True,
                '_source': [''],
                'query': {
                    'bool': {
                        'must': [{
                            'exists': {
                                'field': 'raw'
                            }
                        }, {
                            **dt_query['query']['bool']['must']
                        }]
                    }
                }
            },
            'backfill': {
                'track_total_hits': True,
                '_source': [''],
                'query': {
                    'bool': {
                        'must_not': [{
                            'exists': {
                                'field': 'contents'
                            }
                        }],
                        **dt_query['query']['bool']
                    }
                }
            }
        }

        doc_list = defaultdict(list)

        self.es['corpus'].dump_index(index=index, query=query['corpus'], result=doc_list['corpus'])
        self.es['backfill'].dump_index(index=index, query=query['backfill'], result=doc_list['backfill'])

        return doc_list

    @staticmethod
    def common_docs(doc_list: defaultdict(list)) -> defaultdict(list):
        ids = {
            'corpus': set((x['_index'], x['_id']) for x in doc_list['corpus']),
            'backfill': set((x['_index'], x['_id']) for x in doc_list['backfill']),
        }

        ids['common'] = list(ids['backfill'].intersection(ids['corpus']))

        # missing = {
        #     'corpus': list(ids['backfill'].difference(ids['corpus'])),
        #     'backfill': list(ids['corpus'].difference(ids['backfill'])),
        # }

        # summary = {
        #     'count': {col: f'{len(x):,}' for col, x in doc_list.items()},
        #     'missing': {col: f'{len(x):,}' for col, x in missing.items()}
        # }

        result = defaultdict(list)
        for index, doc_id in ids['common']:
            result[index].append(doc_id)

        return result

    def save_docs(self, index: str, ids: list, size: int) -> None:
        for i in tqdm(range(0, len(ids), size), desc=index):
            id_list = ids[i:i + size]

            docs = []
            self.es['corpus'].get_by_ids(
                index=index,
                id_list=id_list,
                result=docs,
                source=['raw', 'content']
            )

            bulk = []
            for x in docs:
                if 'raw' not in x or 'content' not in x:
                    continue

                bulk += [{
                    'update': {
                        '_id': x['_id'],
                        '_index': index,
                    }
                }, {
                    'doc': {
                        'raw': x['raw'],
                        'contents': x['content'],
                    },
                    'doc_as_upsert': False,
                }]

            _ = self.es['backfill'].conn.bulk(
                index=index,
                body=bulk,
                refresh=True,
                params={'request_timeout': 620}
            )

        return

    def batch(self) -> None:
        self.params = self.init_arguments()

        doc_list = self.dump(
            index=self.params['index'],
            date_range=self.params['date_range']
        )

        common_docs = self.common_docs(doc_list=doc_list)

        for index, ids in common_docs.items():
            self.save_docs(index=index, ids=ids, size=self.params['size'])

        return

    @staticmethod
    def init_arguments() -> dict:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--index', default='crawler-naver-*-2021', type=str)
        parser.add_argument('--date-range', default='2021-03-01~2021-03-05', type=str)

        parser.add_argument('--size', default=300, type=int)

        return vars(parser.parse_args())


if __name__ == '__main__':
    Backfill().batch()
