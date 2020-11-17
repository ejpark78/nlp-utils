#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys

import pandas as pd
from utils.elasticsearch_utils import ElasticSearchUtils
from tqdm.autonotebook import tqdm

MESSAGE = 25
logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)


class DictionaryUtils(object):
    """ """

    def __init__(self):
        """ """
        host_info = {
            'host': 'https://corpus.ncsoft.com:9200',
            'http_auth': 'crawler:crawler2019',
        }

        self.elastic = ElasticSearchUtils(**host_info)

    @staticmethod
    def set_plt_font():
        """matplotlib 한글 폰트 설정"""
        import matplotlib as mpl
        from matplotlib import font_manager, rc

        # 한글 폰트 설정
        font_path = '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf'

        font_name = font_manager.FontProperties(fname=font_path).get_name()
        rc('font', family=font_name)

        mpl.rcParams.update({
            'text.color': 'black',
            'xtick.color': 'white',
            'ytick.color': 'white',
            'axes.labelcolor': 'black',
        })

        return

    def dump_data(self, index, category):
        """ """
        query = {
            '_source': ['document_id', 'category', 'entry_search'],
            'query': {
                'match': {
                    'category': category
                }
            }
        }

        if category == '':
            del query['query']

        doc_list = []
        self.elastic.export(index=index, result=doc_list, query=query)

        return doc_list

    @staticmethod
    def flatten(df):
        """ """
        df = df.reset_index()

        doc_list = {}
        for i, row in tqdm(df.iterrows(), total=len(df)):
            lang = row['category']

            if lang not in doc_list:
                doc_list[lang] = {}

            column = [x for x in row.keys() if x.find('2020-') == 0]
            count = row[column]

            if row['entry_search'] == 'done':
                doc_list[lang]['검색 완료'] = count
            else:
                doc_list[lang]['검색 전'] = count

        df = pd.DataFrame(doc_list).fillna(0).transpose()

        df['합계'] = df.sum(axis=1)
        df.at['합계', :] = df.sum(axis=0)

        # df['수량'] = df.apply(lambda x: '{:,}'.format(x['수량']), axis=1)

        return df.astype('int').style.format('{:,}').set_properties(**{'text-align': 'right'})
