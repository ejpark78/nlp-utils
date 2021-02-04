#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json

import urllib3
from tqdm import tqdm

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class UpdateIndex(object):

    def __init__(self):
        self.logger = Logger()

        self.es = ElasticSearchUtils(host='https://corpus.ncsoft.com:9200', http_auth='crawler:crawler2019')

    @staticmethod
    def mapping_col(doc: dict, col_mapping: dict) -> dict:
        for col in col_mapping:
            if col not in doc:
                continue

            t = col_mapping[col]
            if t != '':
                doc[t] = doc[col]

            del doc[col]

        return doc

    def upload_data(self, filename: str, size: int = 3000) -> None:
        q_index = 'raw-jisikman-question'
        a_index = 'raw-jisikman-answer'

        col_mapping = {
            'answer_count': 'count',
            'answer_content': 'answer',
            'question_content': 'question',
            'answer_source': 'source',
            'tag_string': 'tags',
            **{x: '' for x in '_id,_index,content_id,document_id,detail_answers,reg_date'.split(',')},
        }

        bulk = []
        with bz2.open(filename, 'rt') as fp:
            for line in tqdm(fp, desc=filename.split('/')[-1]):
                doc = json.loads(line)
                if 'settings' in doc and 'mappings' in doc:
                    continue

                q_id = doc['_id']
                detail_answers = doc['detail_answers']

                doc = self.mapping_col(doc=doc, col_mapping=col_mapping)

                if 'question' not in doc or doc['question'] is None:
                    continue

                if '[꿀' in doc['question']:
                    continue

                if 'answer' in doc:
                    del doc['answer']

                bulk += [
                    {
                        'index': {
                            '_id': q_id,
                            '_index': q_index,
                        }
                    },
                    doc
                ]

                for i, answer in enumerate(detail_answers):
                    answer = self.mapping_col(doc=answer, col_mapping=col_mapping)
                    del answer['question']

                    if ' 환불]' in answer['answer']:
                        continue

                    answer['question_id'] = q_id

                    bulk += [
                        {
                            'index': {
                                '_id': '{q_id}-{i:03d}'.format(q_id=q_id, i=i),
                                '_index': a_index,
                            }
                        },
                        answer
                    ]

                if len(bulk) > size:
                    _ = self.es.conn.bulk(index=q_index, body=bulk, refresh=True)
                    bulk = []

            if len(bulk) > 0:
                _ = self.es.conn.bulk(index=q_index, body=bulk, refresh=True)

        return

    def batch(self) -> None:
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2018.json.bz2')
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2017.json.bz2')
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2016.json.bz2')
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2015.json.bz2')
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2014.json.bz2')
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2013.json.bz2')
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2012.json.bz2')
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2011.json.bz2')
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2010.json.bz2')
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2009.json.bz2')
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2008.json.bz2')
        self.upload_data(filename='data/news/jisikman/crawler-jisikman-2007.json.bz2')

        return


if __name__ == '__main__':
    UpdateIndex().batch()
