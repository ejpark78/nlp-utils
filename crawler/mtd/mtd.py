#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os.path import splitext

from nlplab.utils.elasticsearch_utils import ElasticSearchUtils

from .cache_utils import CacheUtils


class MtdCrawler(object):

    def __init__(self):
        super().__init__()

        self.params = self.init_arguments()

    def download(self):
        with open(self.params.meta, 'r') as fp:
            meta = json.load(fp)

        es = ElasticSearchUtils()
        for item in meta['index_list']:
            filename = f"data/mtd/{item['index']}.db"
            db = CacheUtils(filename=filename)

            columns = item['columns'].split(',')
            if 'date_columns' in item:
                columns += item['date_columns'].split(',')

            db.export_index(
                es=es,
                index=item['index'],
                columns=','.join(columns)
            )

            alias = item['column_alias'] if 'column_alias' in item else None
            result_columns = [x for x in columns if x not in alias.keys()]

            if alias is not None:
                result_columns += alias.values()

            f_name = splitext(self.params.cache)[0]
            db.export_tbl(
                filename='{f_name}.json.bz2'.format(f_name=f_name),
                tbl='idx',
                db_column='id,idx,content',
                json_columns='content'.split(','),
                columns=result_columns,
                alias=alias
            )
            db.json2xlsx(filename=f_name)

        return

    def batch(self):
        if self.params.download is True:
            self.download()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--download', action='store_true', default=False, help='내보내기')

        parser.add_argument('--meta', default='./data/mtd/mtd-meta.json', help='메타 파일명')

        return parser.parse_args()


if __name__ == '__main__':
    MtdCrawler().batch()
