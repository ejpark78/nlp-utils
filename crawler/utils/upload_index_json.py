#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json

import urllib3
from dateutil.parser import parse as parse_date
from tqdm import tqdm
from dotty_dict import dotty

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class FilloutHtmlColumn(object):

    def __init__(self):
        self.logger = Logger()

        self.es = ElasticSearchUtils(host='https://corpus.ncsoft.com:9200', http_auth='crawler:crawler2019')

    @staticmethod
    def wrapping_doc(doc: dict, col_mapping: dict) -> dict:
        dot = dotty(doc)

        result = {}
        for col in col_mapping:
            if dot.get(col) is None:
                continue

            t = col_mapping[col]
            if t == '':
                dot.pop(col)
                continue

            result[t] = dot[col]

        if 'date' in result and isinstance(result['date'], str):
            result['date'] = parse_date(result['date']).isoformat()

        result['json'] = json.dumps(dot.to_dict(), ensure_ascii=False)

        return result

    def upload_data(self, filename: str, index: str, size: int = 3000) -> None:
        col_mapping = {
            'title': 'title',
            'ko': 'ko',
            'en': 'en',
            'zh-CN': 'cn',
            **{x: '' for x in '_id,_index,document_id'.split(',')},
        }

        bulk = []
        with bz2.open(filename, 'rt') as fp:
            for line in tqdm(fp, desc=filename.split('/')[-1].replace('.json.bz2', '') + ' -> ' + index):
                doc = json.loads(line)
                if 'settings' in doc and 'mappings' in doc:
                    continue

                doc_id = doc['_id']

                # reply = []
                # if 'reply' in doc:
                #     reply = doc['reply']
                #     del doc['reply']

                new_doc = self.wrapping_doc(doc=doc, col_mapping=col_mapping)

                bulk += [
                    {
                        'index': {
                            '_id': doc_id,
                            '_index': index,
                        }
                    },
                    new_doc
                ]

                # for i, r in enumerate(reply):
                #     r.update({'parent_id': doc_id})
                #
                #     bulk += [
                #         {
                #             'index': {
                #                 '_id': '{}-{:03d}'.format(doc_id, i),
                #                 '_index': index + '-reply',
                #             }
                #         },
                #         r
                #     ]

                if len(bulk) > size:
                    _ = self.es.conn.bulk(index=None, body=bulk, refresh=True)
                    bulk = []

            if len(bulk) > 0:
                _ = self.es.conn.bulk(index=None, body=bulk, refresh=True)

        return

    def batch(self) -> None:
        self.upload_data(filename='data/news/youtube/crawler-youtube-subtitle.json.bz2', index='raw-youtube-subtitle')

        return


if __name__ == '__main__':
    FilloutHtmlColumn().batch()
