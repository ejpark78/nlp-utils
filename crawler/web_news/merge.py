#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json

import pytz
from tqdm import tqdm

from crawler.utils.logger import Logger


class MergeIndex(object):

    def __init__(self):
        self.params = None

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

    @staticmethod
    def mapping_alias(doc: dict, alias: list) -> dict:
        for f, t in alias:
            if f not in doc:
                continue

            doc[t] = doc[f]
            del doc[f]

        return doc

    @staticmethod
    def exclude_columns(doc: dict, exclude: set) -> dict:
        return {k: v for k, v in doc.items() if k not in exclude}

    def batch(self) -> None:
        self.params = self.init_arguments()

        alias = [
            ('@curl_list', '@list_crawl_date'),
            ('@curl_date', '@contents_crawl_date'),
            ('@date', '@contents_crawl_date'),
        ]

        data = {}
        with bz2.open(self.params['backfill'], 'rb') as fp:
            for line in tqdm(fp, desc=self.params['backfill'].split('/')[-1]):
                doc = json.loads(line.decode('utf-8'))

                if 'settings' in doc and 'mappings' in doc:
                    continue

                data[doc['_id']] = self.mapping_alias(doc=doc, alias=alias)

        with bz2.open(self.params['corpus'], 'rb') as fp:
            for line in tqdm(fp, desc=self.params['corpus'].split('/')[-1]):
                doc = json.loads(line.decode('utf-8'))

                if 'settings' in doc and 'mappings' in doc:
                    continue

                if 'content' not in doc and 'contents' not in doc:
                    continue

                doc_id = doc['_id']
                if doc_id not in data:
                    if self.params['missing']:
                        print(json.dumps(doc, ensure_ascii=False), flush=True)
                    continue

                if self.params['missing']:
                    continue

                exclude = set(data[doc_id].keys()) | {'content', 'contents'} - {'raw'}
                raw = self.exclude_columns(doc=doc, exclude=exclude)

                item = {
                    **data[doc_id],
                    'raw': json.dumps(raw, ensure_ascii=False),
                    'contents': doc['content'] if 'content' in doc else doc['contents'],
                    'status': 'merged'
                }

                print(json.dumps(item, ensure_ascii=False), flush=True)

        return

    @staticmethod
    def init_arguments() -> dict:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--missing', action='store_true', default=False)

        parser.add_argument('--backfill', type=str,
                            default='data/es_dump/backfill/latest/crawler-naver-opinion-2014.json.bz2')
        parser.add_argument('--corpus', type=str,
                            default='data/es_dump/corpus/latest/crawler-naver-opinion-2014.json.bz2')

        return vars(parser.parse_args())


if __name__ == '__main__':
    MergeIndex().batch()
