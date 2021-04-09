#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
from os.path import isfile

from tqdm import tqdm


class SplitColumns(object):

    def __init__(self):
        pass

    @staticmethod
    def rename_columns(doc: dict, col_mapping: dict) -> dict:
        for col in col_mapping:
            if col not in doc:
                continue

            t = col_mapping[col]
            if t != '':
                doc[t] = doc[col]

            del doc[col]

        return doc

    def split_columns(self, filename: str, tag: str, year: int, path: str) -> None:
        if isfile(filename) is False:
            return

        columns = {
            'rename': {
                '_id': 'article_id',
                'content': 'contents',
                **{x: '' for x in '_index,document_id,url,raw,html_content,reply_list'.split(',')},
            },
            'split': 'reply_list'
        }

        fp_out = {
            'article': bz2.open(f"{path}/{tag}-{year}.json.bz2", 'wb'),
            'reply': bz2.open(f"{path}/{tag}-reply-{year}.json.bz2", 'wb'),
        }

        with bz2.open(filename, 'rt') as fp:
            for line in tqdm(fp, desc=filename.split('/')[-1]):
                doc = json.loads(line)
                if 'settings' in doc and 'mappings' in doc:
                    continue

                doc_id = doc['_id']
                split_data = doc[columns['split']] if columns['split'] in doc else []

                doc = self.rename_columns(doc=doc, col_mapping=columns['rename'])
                fp_out['article'].write(f'{json.dumps(doc, ensure_ascii=False)}\n'.encode('utf-8'))

                for i, item in enumerate(split_data):
                    item = self.rename_columns(doc=item, col_mapping=columns['rename'])

                    item['_id'] = f'{doc_id}-{i:03d}'
                    item['article_id'] = doc_id

                    fp_out['reply'].write(f'{json.dumps(item, ensure_ascii=False)}\n'.encode('utf-8'))

        for _, fp in fp_out.items():
            fp.flush()
            fp.close()

        return

    def batch(self) -> None:
        tag = 'kbo'
        for year in range(2021, 2010, -1):
            self.split_columns(
                tag=tag,
                year=year,
                filename=f'data/es_dump/corpus/2021-03-21/crawler-bbs-mlbpark_{tag}-{year}.json.bz2',
                path='corpus/data/datasets/mlbpark'
            )

        tag = 'mlb'
        for year in range(2021, 2016, -1):
            self.split_columns(
                tag=tag,
                year=year,
                filename=f'data/es_dump/corpus/2021-03-21/crawler-bbs-mlbpark_{tag}-{year}.json.bz2',
                path='corpus/data/datasets/mlbpark'
            )

        tag = 'bullpen'
        for year in range(2021, 2015, -1):
            self.split_columns(
                tag=tag,
                year=year,
                filename=f'data/es_dump/corpus/2021-03-21/crawler-bbs-mlbpark_{tag}-{year}.json.bz2',
                path='corpus/data/datasets/mlbpark'
            )

        return


if __name__ == '__main__':
    SplitColumns().batch()
