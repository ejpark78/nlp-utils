#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.web_news.cache_utils import CacheUtils


class DumpIndexData(object):

    def __init__(self):
        super().__init__()

        self.params = None

    def batch(self) -> None:
        self.params = self.init_arguments()

        if self.params.dump_index is True:
            elastic = ElasticSearchUtils(host=self.params.host, http_auth=self.params.auth)
            elastic.dump_index(index=self.params.index, size=self.params.size)

        if self.params.json2db is True:
            CacheUtils().json2db(filename=self.params.filename)

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--dump-index', action='store_true', default=False)
        parser.add_argument('--json2db', action='store_true', default=False)

        parser.add_argument('--host', default='https://corpus.ncsoft.com:9200', help='elasticsearch url')
        parser.add_argument('--auth', default='elastic:nlplab', help='elasticsearch auth')

        parser.add_argument('--filename', default=None, help='json file name')
        parser.add_argument('--index', default=None, help='elasticsearch index name')
        parser.add_argument('--size', default=1000, type=int, help='bulk size')

        return parser.parse_args()


if __name__ == '__main__':
    DumpIndexData().batch()
