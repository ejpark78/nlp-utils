#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
from uuid import uuid4

import pandas as pd
from tqdm.autonotebook import tqdm

from utils import ElasticSearchUtils


class BitextExports(object):
    """ """

    def __init__(self):
        """ """
        host_info = {
            'host': 'https://corpus.ncsoft.com:9200',
            'http_auth': 'elastic:nlplab',
        }

        self.utils = ElasticSearchUtils(**host_info)

    @staticmethod
    def save(df, filename):
        """ """
        df.to_json(
            filename,
            force_ascii=False,
            compression='bz2',
            orient='records',
            lines=True,
        )
        return

    @staticmethod
    def read(filename, columns=None):
        """ """
        df = pd.read_json(
            filename,
            compression='bz2',
            orient='records',
            lines=True,
        )

        if columns is None:
            return df

        return df[[x for x in df.columns if x in columns]]

    @staticmethod
    def clean_lang(df):
        """ """
        bitext_df = df.fillna('').groupby(by=['english', 'korean', 'theme', 'level', 'source'])

        bitext_df = bitext_df.size().to_frame().reset_index()
        bitext_df = bitext_df[['theme', 'level', 'source', 'korean', 'english']]

        bitext_df = bitext_df[
            (bitext_df['korean'] != '') &
            (bitext_df['korean'].str.contains('[ㄱ-ㅣ가-힣]+', regex=True, na=False)) &
            (bitext_df['english'] != '') &
            ~(bitext_df['english'].str.contains('[ㄱ-ㅣ가-힣]+', regex=True, na=False))
            ]

        return bitext_df

    def export_example(self):
        """ """
        index = 'crawler-naver-dictionary-example'

        query = {
            '_source': ['expExample1', 'expExample2']
        }

        doc_list = []
        self.utils.export(index=index, query=query, result=doc_list)

        df = pd.DataFrame(doc_list).fillna('')
        df = df.rename(columns={'expExample1': 'english', 'expExample2': 'korean'})

        df.at[:, 'level'] = ''
        df.at[:, 'theme'] = '사전 예문'
        df.at[:, 'source'] = 'example'

        bitext_df = self.clean_lang(df=df)

        self.save(df=bitext_df, filename=f'dictionary/{index}.bitext.json.bz2')

        return bitext_df

    def export_user_translation(self):
        """ 사용자 참여 번역 """
        index = 'crawler-naver-dictionary-user-translation'

        query = {
            '_source': ['sentence1', 'sentence2', 'theme', 'level']
        }

        doc_list = []
        self.utils.export(index=index, result=doc_list, query=query)

        df = pd.DataFrame(doc_list).fillna('')
        df = df.rename(columns={'sentence1': 'english', 'sentence2': 'korean'})

        df.at[:, 'source'] = 'user-translation'

        bitext_df = self.clean_lang(df=df)

        self.save(df=bitext_df, filename=f'dictionary/{index}.bitext.json.bz2')

        return bitext_df

    def export_today_conversation(self):
        """ 오늘의 회화 """
        index = 'crawler-naver-conversation'

        query = {
            '_source': ['sentences.orgnc_sentence', 'sentences.trsl_orgnc_sentence']
        }

        doc_list = []
        self.utils.export(index=index, result=doc_list, query=query)

        sentences = []
        for doc in doc_list:
            for sent in doc['sentences']:
                sentences.append(sent)

        df = pd.DataFrame(sentences).fillna('')
        df = df.rename(columns={'orgnc_sentence': 'english', 'trsl_orgnc_sentence': 'korean'})

        df['korean'] = df['korean'].apply(lambda x: re.sub('(<b>|</b>)', '', x))
        df['english'] = df['english'].apply(lambda x: re.sub('(<b>|</b>)', '', x))

        df.at[:, 'level'] = ''
        df.at[:, 'theme'] = '오늘의 회화'
        df.at[:, 'source'] = 'conversation'

        bitext_df = self.clean_lang(df=df)

        self.save(df=bitext_df, filename=f'dictionary/{index}.bitext.json.bz2')

        return bitext_df

    def export_news(self):
        """ """
        index_list = {
            'corpus-bitext-cnn': {'theme': 'news', 'source': 'cnn'},
            'corpus-bitext-ted': {'theme': 'speech', 'source': 'ted'},
            'corpus-bitext-kusk': {'theme': 'news', 'source': 'kusk'},
            'corpus-bitext-donga': {'theme': 'news', 'source': 'donga'},
        }

        query = {
            '_source': ['korean', 'english']
        }

        for index in index_list:
            doc_list = []
            self.utils.export(index=index, result=doc_list, query=query)

            df = pd.DataFrame(doc_list).fillna('')

            df.at[:, 'level'] = ''
            for col in index_list[index]:
                df.at[:, col] = index_list[index][col]

            bitext_df = self.clean_lang(df=df)

            self.save(df=bitext_df, filename=f'news/{index}.bitext.json.bz2')

        return

    def import_bitext(self, filename, index):
        """ """
        columns = [
            'theme',
            'level',
            'source',
            'style',
            'korean',
            'korean_morp',
            'korean_token',
            'english',
            'english_morp',
            'english_token',
        ]

        df = self.read(filename=filename, columns=columns)

        for i, row in tqdm(df.iterrows(), total=len(df), desc=filename):
            doc = dict(row)
            doc['_id'] = str(uuid4())

            self.utils.save_document(index=index, document=doc)

        self.utils.flush()

        return df
