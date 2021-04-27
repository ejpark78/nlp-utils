#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
from os import remove, sync
from os.path import isfile

from berkeleydb import hashopen

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

    def merge(self) -> None:
        alias = [
            ('content', 'contents'),
            ('@date', '@contents_crawl_date'),
            ('@curl_list', '@list_crawl_date'),
            ('@curl_date', '@contents_crawl_date'),
        ]

        cache_db = {}
        if self.params['use_cache']:
            cache_file = self.params['corpus'].replace('.json.bz2', '.db')
            if isfile(cache_file):
                remove(cache_file)
                sync()

            cache_db = hashopen(cache_file, 'w')

        index = self.params['corpus'].split('/')[-1].replace('.json.bz2', '')

        # read corpus index
        with bz2.open(self.params['corpus'], 'rb') as fp:
            for line in tqdm(fp, desc=f'corpus: {index}'):
                doc = json.loads(line.decode('utf-8'))

                if 'settings' in doc and 'mappings' in doc:
                    continue

                doc_id = doc['_id']
                val = self.mapping_alias(doc=doc, alias=alias)

                if self.params['use_cache']:
                    val = json.dumps(val, ensure_ascii=False).encode('utf-8')
                    doc_id = doc_id.encode('utf-8')

                cache_db[doc_id] = val

        if self.params['use_cache']:
            cache_db.sync()

        # read backfill index
        with bz2.open(self.params['backfill'], 'rb') as fp:
            for line in tqdm(fp, desc=f'backfill: {index}'):
                doc = json.loads(line.decode('utf-8'))

                if 'settings' in doc and 'mappings' in doc:
                    continue

                doc_id = doc['_id']
                if self.params['use_cache']:
                    doc_id = doc_id.encode('utf-8')

                doc = self.mapping_alias(doc=doc, alias=alias)

                item = doc
                if doc_id in cache_db:
                    cache_doc = cache_db[doc_id]
                    if self.params['use_cache']:
                        cache_doc = json.loads(cache_db[doc_id].decode('utf-8'))

                    if 'contents' in cache_doc:
                        doc['contents'] = cache_doc['contents']

                    raw = self.exclude_columns(doc=cache_doc, exclude=set(doc.keys()) | {'contents'})
                    item = {
                        **doc,
                        'raw': json.dumps(raw, ensure_ascii=False),
                        'status': 'merged'
                    }

                    del cache_db[doc_id]
                elif self.params['missing']:
                    print(json.dumps(doc, ensure_ascii=False), flush=True)

                print(json.dumps(self.change_status(doc=item), ensure_ascii=False), flush=True)

        if self.params['use_cache']:
            cache_db.close()

        return

    def dump_cache_db(self) -> None:
        if not isfile(self.params['cache']):
            return

        cache_db = hashopen(self.params['cache'], 'r')

        for k, val in cache_db.items():
            print(json.dumps(json.loads(val.decode('utf-8')), ensure_ascii=False), flush=True)

        cache_db.close()

        return

    def batch(self) -> None:
        self.params = self.init_arguments()

        if self.params['dump_cache']:
            self.dump_cache_db()
        else:
            self.merge()

        return

    @staticmethod
    def init_arguments() -> dict:
        import argparse

        parser = argparse.ArgumentParser()

        # merge
        parser.add_argument('--missing', action='store_true', default=False)
        parser.add_argument('--use-cache', action='store_true', default=False)

        parser.add_argument('--backfill', type=str, default=None)
        parser.add_argument('--corpus', type=str, default=None)

        # dump cache
        parser.add_argument('--dump-cache', action='store_true', default=False)

        parser.add_argument('--cache', type=str, default=None)

        return vars(parser.parse_args())


if __name__ == '__main__':
    MergeIndex().batch()
