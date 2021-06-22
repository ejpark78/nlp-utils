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

from crawler.utils.es import ElasticSearchUtils
from crawler.utils.logger import Logger
from dotty_dict import dotty
from urllib.parse import unquote
from base64 import b64decode

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class SplitColumns(object):

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
            'date': 'date',
            'contents': 'text',
            'writer_id': 'name',
            'object_id': 'game_id',
            'team_name': 'team_name',
            **{x: '' for x in '_id,_index,document_id'.split(',')},
        }

        bulk = []
        with bz2.open(filename, 'rt') as fp:
            for line in tqdm(fp, desc=filename.split('/')[-1].replace('.json.bz2', '') + ' -> ' + index):
                doc = json.loads(line)
                if 'settings' in doc and 'mappings' in doc:
                    continue

                idx = index.replace('-{year}', '')
                if 'date' in doc:
                    idx = index.format(year=parse_date(doc['date']).year)

                doc_id = doc['_id']
                new_doc = self.wrapping_doc(doc=doc, col_mapping=col_mapping)

                bulk += [
                    {
                        'index': {
                            '_id': doc_id,
                            '_index': idx,
                        }
                    },
                    new_doc
                ]

                if len(bulk) > size:
                    _ = self.es.conn.bulk(index=None, body=bulk, refresh=True)
                    bulk = []

            if len(bulk) > 0:
                _ = self.es.conn.bulk(index=None, body=bulk, refresh=True)

        return

    def batch(self) -> None:
        index = 'raw-naver-kbo-reply-{year}'

        # self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2020.json.bz2', index=index)
        # self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2019.json.bz2', index=index)
        # self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2018.json.bz2', index=index)
        # self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2017.json.bz2', index=index)
        # self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2016.json.bz2', index=index)
        # self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2015.json.bz2', index=index)
        # self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2014.json.bz2', index=index)
        # self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2013.json.bz2', index=index)
        # self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2012.json.bz2', index=index)
        # self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2011.json.bz2', index=index)
        self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2010.json.bz2', index=index)
        self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2009.json.bz2', index=index)
        self.upload_data(filename='data/news/naver-kbo/crawler-naver-kbo_game_center_comments-2008.json.bz2', index=index)

        return


if __name__ == '__main__':
    SplitColumns().batch()
