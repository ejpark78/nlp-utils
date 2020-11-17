#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
from glob import glob

import pytz
from tqdm import tqdm

from utils.elasticsearch_utils import ElasticSearchUtils


class InsertCorpus(object):
    """"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.symbol = {
            'A': 'General Science',
            'B': 'Physics',
            'C': 'Chemistry',
            'D': 'Space/Earth Science',
            'E': 'Biology',
            'F': 'Agriculture',
            'G': 'Medicine',
            'H': 'Engineering',
            'I': 'Systems Engineering',
            'J': 'Computer Science',
            'K': 'Industrial Engineering',
            'L': 'Energy Science',
            'M': 'Nuclear Science',
            'N': 'Electronic Engineering',
            'P': 'Thermodynamics',
            'Q': 'Mechanical Engineering',
            'R': 'Construction',
            'S': 'Environmental Science',
            'T': 'Transportation Engineering',
            'U': 'Mining Engineering',
            'W': 'Metal Engineering',
            'X': 'Chemical Engineering',
            'Y': 'Chemical Manufacturing',
            'Z': 'Other',
        }

    def jaen(self):
        """ """
        index = 'corpus-bitext-aspec-jaen'

        elastic = ElasticSearchUtils(
            host='https://corpus.ncsoft.com:9200',
            index=index,
            http_auth='elastic:nlplab',
        )

        path = 'data/aspec.en-jp/ASPEC/ASPEC-JE/*/*.bz2'

        columns = {
            5: 'doc_name,no,ja_text,en_text,role'.split(','),
            6: 'similarity,doc_name,no,ja_text,en_text,role'.split(',')
        }

        for filename in tqdm(glob(path)):
            role = filename.split('/')[-2]

            with bz2.open(filename, 'rb') as fp:
                for line in tqdm(fp.readlines(), desc=filename):
                    token = [x.strip() for x in line.decode('utf-8').split('|||')] + [role]
                    doc = dict(zip(columns[len(token)], token))

                    doc['category'], doc['doc_name'] = doc['doc_name'].split('-', maxsplit=1)

                    if doc['category'] in self.symbol:
                        doc['category'] = self.symbol[doc['category']]

                    doc['_id'] = '{}-{}'.format(doc['doc_name'], doc['no'])

                    elastic.save_document(document=doc, index=index)

                elastic.flush()

        return

    def batch(self):
        """ """
        index = 'corpus-bitext-aspec-jazh'

        elastic = ElasticSearchUtils(
            host='https://corpus.ncsoft.com:9200',
            index=index,
            http_auth='elastic:nlplab',
        )

        path = 'data/aspec.en-jp/ASPEC/ASPEC-JC/*/*.bz2'

        columns = {
            4: 'sentence_id,ja_text,zh_text,role'.split(','),
        }

        for filename in tqdm(glob(path)):
            role = filename.split('/')[-2]

            with bz2.open(filename, 'rb') as fp:
                for line in tqdm(fp.readlines(), desc=filename):
                    token = [x.strip() for x in line.decode('utf-8').split('|||')] + [role]
                    doc = dict(zip(columns[len(token)], token))

                    doc['_id'] = doc['sentence_id']

                    elastic.save_document(document=doc, index=index)

                elastic.flush()

        return


if __name__ == '__main__':
    InsertCorpus().batch()
