#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import pandas as pd
from tqdm import tqdm

from utils.elasticsearch_utils import ElasticSearchUtils


class ChattingLogUtils(object):
    """ """

    def __init__(self):
        """ """
        host_info = {
            'host': 'https://corpus.ncsoft.com:9200',
            'http_auth': 'elastic:nlplab',
        }

        self.elastic = ElasticSearchUtils(**host_info)

        self.titles = {
            'BS': ['doc_id', 'category', 'writer_id', 'serverno', 'char_id', 'post_time', 'contents']
        }

    def read_file(self, filename, meta):
        """ """
        if filename.find('.txt.bz2') > 0:
            with bz2.open(filename, 'r') as fp:
                contents = [{'contents': x.decode('utf-8').strip()} for x in fp.readlines()]

            df = pd.DataFrame(contents)
        elif filename.find('.csv') > 0:
            df = pd.read_csv(filename, sep=',', compression='bz2')
        elif filename.find('.tsv') > 0:
            if meta['game_name'] not in 'BS':
                df = pd.read_csv(filename, sep='\t', compression='bz2')
            else:
                df = pd.read_csv(filename, sep='\t', header=0, names=self.titles['BS'], compression='bz2')

        return df.fillna('')

    @staticmethod
    def split_contents(df, meta):
        """ """
        import pytz
        from dateutil.parser import parse as parse_date

        tz = pytz.timezone('Asia/Seoul')

        result = []

        for i, row in df.iterrows():
            doc = dict(row)

            for k in doc:
                if k.find('time') > 0:
                    doc[k] = parse_date(doc[k]).astimezone(tz).isoformat()

            doc.update(meta)
            if isinstance(doc['contents'], str) and doc['contents'].find('||'):
                doc['contents'] = doc['contents'].replace('||', ' / ')

            contents_list = [doc['contents']]
            if isinstance(doc['contents'], str):
                # ESC = '\x1b'
                contents = doc['contents']
                contents = contents.replace(u'\x1b', '')
                contents = contents.replace(u'\x3C', ' ')

                contents_list = contents.split(' / ')

            del doc['contents']

            for text in contents_list:
                doc['text'] = text
                if isinstance(text, str):
                    doc['text'] = text.strip()

                if doc['text'] == '' or doc['text'] is None:
                    continue

                item = {}
                for k in doc:
                    item[k] = doc[k]

                result.append(item)

        return result

    def insert_row(self, doc_list):
        """ """
        from uuid import uuid4

        uid = str(uuid4())[:8]
        index = 'corpus-game-chatting-logs'

        count = 1
        for doc in tqdm(doc_list):
            doc['_id'] = '{}-{:07d}'.format(uid, count)
            count += 1

            self.elastic.save_document(document=doc, index=index)

        self.elastic.flush()

        return

    @staticmethod
    def get_meta(text):
        """ """
        text = text.replace('.', '_')
        text = text.replace('_', '/')

        token = text.split('/')[:-1]
        if token[-3].isdecimal() is True:
            token[-2] = '{}~{}'.format(token[-3], token[-2])
            del token[-3]

        return {
            'game_name': token[2],
            'lang': token[3],
            'date': token[-2],
            'format': token[-1],
        }

    def batch(self, f_list):
        """ """
        p_bar = tqdm(f_list)
        for f in p_bar:
            p_bar.set_description_str(f)

            meta = self.get_meta(text=f)

            df = self.read_file(filename=f, meta=meta)
            doc_list = self.split_contents(df=df, meta=meta)

            self.insert_row(doc_list=doc_list)

        return


def main():
    """"""
    from glob import glob

    f_list = glob('game_logs/*/??/*.*')

    ChattingLogUtils().batch(f_list)

    return


if __name__ == '__main__':
    main()
