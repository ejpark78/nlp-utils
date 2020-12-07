#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

from tqdm import tqdm

from utils.selenium_utils import SeleniumUtils
from utils.elasticsearch_utils import ElasticSearchUtils


class FBSplitLang(SeleniumUtils):
    """ ko 에 저장된 영어 그룹을 분리 """

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.elastic = None

    def open_db(self):
        """ 디비를 연결한다."""
        self.elastic = ElasticSearchUtils(
            host=self.env.host,
            index=self.env.index,
            log_path=self.env.log_path,
            http_auth=self.env.auth,
            split_index=True,
        )
        return

    @staticmethod
    def to_string(doc):
        """ 문서의 각 필드값을 string 타입으로 변환한다. """
        for k in doc:
            if isinstance(doc[k], str) is True:
                continue

            if isinstance(doc[k], dict) is True or isinstance(doc[k], list) is True:
                doc[k] = json.dumps(doc[k])
                continue

            doc[k] = str(doc[k])

        return doc

    def batch(self):
        """ """
        self.env = self.init_arguments()

        self.open_db()

        from_index = self.env.from_index
        to_index = self.env.to_index

        doc_list = self.elastic.dump(index=from_index)

        bulk_data = {
            'insert': [],
            'delete': [],
        }
        for doc in tqdm(doc_list):
            doc['content'] = doc['content'].replace('\n… \n더 보기\n', '')

            doc = self.to_string(doc=doc)

            bulk_data['insert'] += [
                {
                    'update': {
                        '_id': doc['document_id'],
                        '_index': to_index,
                    }
                },
                {
                    'doc': doc,
                    'doc_as_upsert': True,
                }
            ]

            bulk_data['delete'] += [
                {
                    'delete': {
                        '_id': doc['document_id'],
                        '_index': from_index,
                    }
                }
            ]

            if len(bulk_data['insert']) > 3000:
                self.flush(bulk_data=bulk_data['insert'], index=from_index)
                self.flush(bulk_data=bulk_data['delete'], index=from_index)

                bulk_data['insert'] = []
                bulk_data['delete'] = []

        if len(bulk_data['insert']) > 0:
            self.flush(bulk_data=bulk_data['insert'], index=from_index)
            self.flush(bulk_data=bulk_data['delete'], index=from_index)

        return

    def flush(self, bulk_data, index):
        """ """
        params = {'request_timeout': 620}

        self.elastic.elastic.bulk(
            index=index,
            body=bulk_data,
            refresh=True,
            params=params,
        )
        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--config', default='config/facebook/group.json')

        parser.add_argument('--from_index', default='crawler-facebook-ko')
        parser.add_argument('--to_index', default='crawler-facebook-ko-new')

        parser.add_argument('--host', default='https://corpus.ncsoft.com:9200')
        parser.add_argument('--auth', default='crawler:crawler2019')
        parser.add_argument('--index', default='crawler-facebook-ko')

        parser.add_argument('--log_path', default='log')

        return parser.parse_args()


if __name__ == '__main__':
    FBSplitLang().batch()
