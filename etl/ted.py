#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
from glob import glob
from os import makedirs
from os.path import isdir

import pytz
import re
import json
from tqdm import tqdm
from bs4 import BeautifulSoup

from utils.elasticsearch_utils import ElasticSearchUtils


class InsertCorpus(object):
    """"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.index = 'corpus-bitext-ted-south_asia'

        self.elastic = ElasticSearchUtils(
            host='https://corpus.ncsoft.com:9200',
            index=self.index,
            http_auth='elastic:nlplab',
        )

    def multilang(self):
        """ """
        filename = 'data/ted/bitext.bz2'

        columns = 'no,lang,text'.split(',')

        with bz2.open(filename, 'rb') as fp:
            buf = []
            for line in tqdm(fp.readlines(), desc=filename):
                line = line.decode('utf-8')

                if re.match(r'^\d+:', line) is None:
                    buf[-1] = buf[-1] + '\n' + line.strip()
                    continue

                buf.append(line.strip())

            index = {}
            for line in tqdm(buf):
                token = [x.strip() for x in line.split(':', maxsplit=2)]
                doc = dict(zip(columns, token))

                if doc['no'] not in index:
                    index[doc['no']] = {}

                index[doc['no']][doc['lang']] = doc['text']

            for no in tqdm(index):
                doc = index[no]
                doc['_id'] = no

                self.elastic.save_document(document=doc, index=self.index)

            self.elastic.flush()

        return

    def split_by_title(self):
        """ """
        path = 'data/ted/xml/ted_*.xml.bz2'

        for filename in tqdm(glob(path)):
            lang = filename.split('-2')[0].split('_')[-1]

            with bz2.open(filename, 'rb') as fp:
                content = ''.join([x.decode('utf-8') for x in tqdm(fp.readlines())])

            soup = BeautifulSoup(content, 'lxml')

            for file in soup.find_all('file'):
                meta = {}
                for tag_name in 'title,url,dtime,keywords,speaker,description'.split(','):
                    tag = file.find(tag_name)
                    if tag is None:
                        continue

                    meta[tag_name] = tag.get_text()

                sent_list = []
                for tag in file.find_all('seekvideo'):
                    sent_list.append({
                        'id': tag['id'],
                        'lang': lang,
                        'text': tag.get_text(),
                    })

                doc = {
                    'meta': meta,
                    'sent_list': sent_list,
                }

                title = meta['url'].split('/')[-1]
                out_path = 'data/ted/json/{}'.format(title)

                if isdir(out_path) is False:
                    makedirs(out_path)

                out_filename = '{}/{}.json'.format(out_path, lang)
                print(out_filename)

                with open(out_filename, 'w') as fp:
                    fp.write(json.dumps(doc, ensure_ascii=False, indent=4))

        return

    def split_by_bitext(self):
        """ """
        path = 'data/ted/json/*'

        self.index = 'corpus-bitext-ted-south_asia-koja'

        pair = {'ko', 'ja'}

        for title in tqdm(glob(path)):
            sentences = self.read_file(title=title)

            lang_list = set()
            if len(lang_list) != len(pair):
                continue

            for no in sentences:
                doc = sentences[no]

                doc['_id'] = '{}-{}'.format(doc['title'], no)

                doc['no'] = no
                doc['title'] = doc['title'].replace('_', ' ')

                self.elastic.save_document(document=doc, index=self.index)

            self.elastic.flush()

        return

    @staticmethod
    def read_file(title):
        """ """
        result = {}

        for filename in tqdm(glob('{}/*.json'.format(title))):
            lang = filename.split('/')[-1].replace('.json', '')

            with open(filename, 'r') as fp:
                doc = json.load(fp)

                for s in doc['sent_list']:
                    s_id = int(s['id'])
                    if s_id not in result:
                        result[s_id] = {}

                    result[s_id][lang] = s['text']
                    result[s_id]['s_id'] = '{:07d}'.format(s_id)
                    result[s_id]['title'] = title.split('/')[-1]

        return result

    def save_docs(self, doc_list):
        """ """
        self.index = 'corpus-bitext-ted-south_asia'

        # pair = {'ko', 'ja'}

        for doc in doc_list:
            doc['_id'] = '{}-{}'.format(doc['title'], doc['s_id'])

            doc['title'] = doc['title'].replace('_', ' ')

            self.elastic.save_document(document=doc, index=self.index)

        self.elastic.flush()

        return

    def merge_text(self):
        """ """
        path = 'data/ted/json/*'

        for title in tqdm(glob(path)):
            sentences = self.read_file(title=title)

            merged = []

            # marge english text
            for s_id, doc in sorted(sentences.items(), key=lambda x: x[0]):
                if len(merged) == 0:
                    merged.append(doc)
                    continue

                prev = merged[-1]
                if 'en' in prev and re.match(r'[a-z,:;\-]', prev['en'][-1]) is not None:
                    for lang in doc:
                        if lang in {'s_id', 'lang', 'title'}:
                            continue

                        if lang in merged[-1]:
                            merged[-1][lang] += ' ' + doc[lang]
                            continue

                        merged[-1][lang] = doc[lang]

                    continue

                merged.append(doc)

            self.save_docs(doc_list=merged)

        return

    def batch(self):
        """ """
        self.merge_text()
        return


if __name__ == '__main__':
    InsertCorpus().batch()
