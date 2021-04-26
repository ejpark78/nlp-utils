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

    @staticmethod
    def change_status(doc: dict) -> dict:
        if 'status' not in doc:
            return doc

        if doc['status'] == 'raw_list':
            doc['status'] = 'list'
            return doc

        return doc

    def batch(self) -> None:
        self.params = self.init_arguments()

        alias = [
            ('content', 'contents'),
            ('@date', '@contents_crawl_date'),
            ('@curl_list', '@list_crawl_date'),
            ('@curl_date', '@contents_crawl_date'),
        ]

        index = self.params['corpus'].split('/')[-1].replace('.json.bz2', '')

        data = {}
        with bz2.open(self.params['corpus'], 'rb') as fp:
            for line in tqdm(fp, desc=f'corpus: {index}'):
                doc = json.loads(line.decode('utf-8'))

                if 'settings' in doc and 'mappings' in doc:
                    continue

                data[doc['_id']] = self.mapping_alias(doc=doc, alias=alias)

        with bz2.open(self.params['backfill'], 'rb') as fp:
            for line in tqdm(fp, desc=f'backfill: {index}'):
                doc = json.loads(line.decode('utf-8'))

                if 'settings' in doc and 'mappings' in doc:
                    continue

                doc_id = doc['_id']
                doc = self.mapping_alias(doc=doc, alias=alias)

                item = doc
                if doc_id in data:
                    if 'contents' in data[doc_id]:
                        doc['contents'] = data[doc_id]['contents']

                    exclude = set(doc.keys()) | {'contents'}
                    raw = self.exclude_columns(doc=data[doc_id], exclude=exclude)

                    item = {
                        **doc,
                        'raw': json.dumps(raw, ensure_ascii=False),
                        'status': 'merged'
                    }

                    del data[doc_id]
                elif self.params['missing']:
                    print(json.dumps(doc, ensure_ascii=False), flush=True)

                item = self.change_status(doc=item)
                print(json.dumps(item, ensure_ascii=False), flush=True)

        if self.params['extra']:
            for doc in data.values():
                print(json.dumps(doc, ensure_ascii=False), flush=True)

        return

    @staticmethod
    def init_arguments() -> dict:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--missing', action='store_true', default=False)
        parser.add_argument('--extra', action='store_true', default=False)

        parser.add_argument('--backfill', type=str,
                            default='data/es_dump/backfill/latest/crawler-naver-opinion-2014.json.bz2')
        parser.add_argument('--corpus', type=str,
                            default='data/es_dump/corpus/latest/crawler-naver-opinion-2014.json.bz2')

        return vars(parser.parse_args())


if __name__ == '__main__':
    MergeIndex().batch()
