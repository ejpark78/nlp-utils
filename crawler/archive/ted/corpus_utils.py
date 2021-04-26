#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from glob import glob
from os import unlink
from os.path import isdir

import pytz
import urllib3
from tqdm import tqdm

from crawler.utils.elasticsearch import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class TedCorpusUtils(object):

    def __init__(self):
        super().__init__()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.index = 'crawler-ted'
        self.elastic = None

    def save_talks(self, talks):
        if self.elastic is None:
            return

        for doc in talks:
            doc['_id'] = f"{doc['talk_id']}-{doc['time']}"

            self.elastic.save_document(document=doc, index=self.index)

        self.elastic.flush()

        return

    @staticmethod
    def read_languages(talk_id):
        filter_lang = {'ko', 'en', 'id', 'vi', 'ja', 'zh-tw', 'zh-cn'}

        result = {}
        lang_list = []
        for filename in tqdm(glob(f'{talk_id}/*.json')):
            if 'talk-info' in filename:
                continue

            lang = filename.split('/')[-1].replace('.json', '')
            if lang not in filter_lang:
                continue

            with open(filename, 'r') as fp:
                content = ''.join(fp.readlines())
                if content.strip() == '':
                    continue

                doc = json.loads(content)

            lang_list.append(lang)

            if 'paragraphs' not in doc:
                if 'error' in doc:
                    unlink(filename)
                    print('error', doc, 'delete', filename)

                continue

            for paragraphs in doc['paragraphs']:
                for item in paragraphs['cues']:

                    s_id = int(item['time'])
                    if s_id not in result:
                        result[s_id] = {}

                    result[s_id][lang] = item['text'].strip().replace('\n', ' ')
                    result[s_id]['time'] = s_id
                    result[s_id]['talk_id'] = talk_id.split('/')[-1]

        return result, lang_list

    def batch(self):
        self.elastic = ElasticSearchUtils(
            host='https://corpus.ncsoft.com:9200',
            index=self.index,
            http_auth='elastic:nlplab',
        )

        path = 'data/ted/*'
        for talk_id in tqdm(glob(path)):
            if isdir(talk_id) is False:
                continue

            sentences, lang_list = self.read_languages(talk_id=talk_id)
            if len(lang_list) < 2:
                continue

            merged = []

            # marge english text
            for s_id, doc in sorted(sentences.items(), key=lambda x: x[0]):
                if len(merged) == 0:
                    merged.append(doc)
                    continue

                prev = merged[-1]
                if 'en' in prev and len(prev['en']) > 0 and re.match(r'[a-z,:;\-]', prev['en'][-1]) is not None:
                    for lang in lang_list:
                        if lang in merged[-1] and lang in doc:
                            merged[-1][lang] += ' ' + doc[lang]
                            continue

                        if lang not in doc:
                            doc[lang] = ''

                        merged[-1][lang] = doc[lang]

                    continue

                merged.append(doc)

            self.save_talks(talks=merged)

        return
