#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import sys
from datetime import datetime
from glob import glob
from os.path import isdir
from uuid import uuid4
from module.utils.logger import LogMessage as LogMsg

import pytz
import requests
import urllib3
from bs4 import BeautifulSoup

from module.utils.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DictionaryUtils(object):
    """사전 예문 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.env = None

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/81.0.4044.113 '
                          'Safari/537.36',
        }

        self.host = 'https://corpus.ncsoft.com:9200'
        self.http_auth = 'crawler:crawler2019'

        self.timezone = pytz.timezone('Asia/Seoul')

        self.elastic = None

        self.MESSAGE = 25
        self.logger = self.get_logger()

        self.skip = 0
        self.cache = set()

    @staticmethod
    def get_values(tag, css, value_type='text'):
        values = tag.select(css)
        if len(values) == 0:
            return ''

        if value_type == 'text':
            return values[0].get_text()
        elif values[0].has_attr('href'):
            return values[0]['href']

        return ''

    def get_logger(self):
        """ """
        logging.addLevelName(self.MESSAGE, 'MESSAGE')
        logging.basicConfig(format='%(message)s')

        self.logger = logging.getLogger()

        self.logger.setLevel(self.MESSAGE)
        self.logger.handlers = [logging.StreamHandler(sys.stderr)]

        return self.logger

    def open_db(self, index):
        """ """
        self.elastic = ElasticSearchUtils(host=self.host, http_auth=self.http_auth, index=index)
        return self.elastic

    def get_html(self, url, resp_type='html'):
        """ """
        headers = self.headers

        headers['Referer'] = url

        resp = requests.get(url, headers=headers, timeout=60, verify=False)
        if resp_type == 'json':
            try:
                return resp.json()
            except Exception as e:
                self.logger.error(msg=LogMsg({
                    'message': 'ERROR resp not json',
                    'exception': str(e),
                    'entry': resp.content,
                }))

                return None

        soup = BeautifulSoup(resp.content, 'html5lib')

        return soup

    @staticmethod
    def parse_url(url):
        """ """
        from urllib.parse import urlparse, parse_qs

        url_info = urlparse(url)

        query = parse_qs(url_info.query)
        for key in query:
            query[key] = query[key][0]

        return query

    @staticmethod
    def read_config(filename):
        """설정파일을 읽어드린다."""
        file_list = [filename]
        if isdir(filename) is True:
            file_list = []
            for f_name in glob('{}/*.json'.format(filename)):
                file_list.append(f_name)

        result = []

        for f_name in file_list:
            with open(f_name, 'r') as fp:
                buf = ''
                for line in fp.readlines():
                    line = line.rstrip()
                    if line.strip() == '' or line[0:2] == '//' or line[0] == '#':
                        continue

                    buf += line
                    if line != '}':
                        continue

                    doc = json.loads(buf)
                    buf = ''

                    result.append(doc)

        return result

    def remove_same_example(self):
        """ """
        # from tqdm import tqdm
        #
        # self.open_db(index=self.env.index)
        #
        # id_list = self.elastic.get_id_list(index=self.env.index)
        # id_list = list(id_list)
        #
        # size = 1000
        #
        # start = 0
        # end = size
        #
        # index = set()
        #
        # bulk_data = []
        # params = {'request_timeout': 2 * 60}
        # columns = self.env.columns.split(',')
        #
        # count = {c: 0 for c in columns}
        #
        # count['total'] = 0
        # count['missing_column'] = 0
        #
        # p_bar = tqdm(total=len(id_list), dynamic_ncols=True)
        #
        # while start < len(id_list):
        #     doc_list = []
        #     self.elastic.get_by_ids(
        #         id_list=id_list[start:end],
        #         index=self.elastic.index,
        #         source=['document_id'] + columns,
        #         result=doc_list
        #     )
        #
        #     for doc in doc_list:
        #         p_bar.update()
        #
        #         count['total'] += 1
        #         if set(doc.keys()).intersection(columns) is False:
        #             count['missing_column'] += 1
        #             continue
        #
        #         text = '\t'.join([doc[k] for k in columns if k in doc])
        #
        #         for k in columns:
        #             if k in doc and doc[k].strip() != '':
        #                 continue
        #
        #             count[k] += 1
        #
        #         if text == '\t' or text in index:
        #             bulk_data.append({
        #                 'delete': {
        #                     '_id': doc['document_id'],
        #                     '_index': self.env.index,
        #                 }
        #             })
        #
        #             if len(bulk_data) > 1000:
        #                 resp = self.elastic.elastic.bulk(
        #                     index=self.env.index,
        #                     body=bulk_data,
        #                     refresh=True,
        #                     params=params,
        #                 )
        #                 print(resp)
        #
        #                 bulk_data = []
        #
        #         index.add(text)
        #
        #     if start >= len(id_list):
        #         break
        #
        #     start = end
        #     end += size
        #
        #     if end > len(id_list):
        #         end = len(id_list)
        #
        # if len(bulk_data) > 0:
        #     resp = self.elastic.elastic.bulk(
        #         index=self.env.index,
        #         body=bulk_data,
        #         refresh=True,
        #         params=params,
        #     )
        #     print(resp)
        #
        # print(count)

        return

    def reset_list(self, column):
        """ """
        self.open_db(self.env.list_index)

        query = {
            '_source': ['state', 'document_id'],
            'query': {
                'bool': {
                    'must': [
                        {
                            'match': {
                                column: 'done'
                            }
                        }
                    ]
                }
            }
        }

        doc_list = self.elastic.dump(query=query)

        for doc in doc_list:
            doc['_id'] = doc['document_id']
            del doc['document_id']

            doc[column] = ''
            self.elastic.save_document(document=doc, index=self.env.list_index)

        self.elastic.flush()

        return

    def set_as_done(self, doc, column):
        """ """
        doc['_id'] = doc['document_id']
        del doc['document_id']

        doc[column] = 'done'
        doc['curl_date'] = datetime.now(self.timezone).isoformat()

        self.elastic.save_document(index=self.env.list_index, document=doc, delete=False)
        self.elastic.flush()
        return

    def read_entry_list(self, lang, column, state_done=True):
        """설정파일을 읽어드린다."""
        self.open_db(self.env.list_index)

        query = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'match': {
                                'lang': lang
                            }
                        }
                    ],
                    'must_not': [
                        {
                            'match': {
                                column: 'done'
                            }
                        }
                    ]
                }
            }
        }

        if state_done is False:
            query = {}

        doc_list = self.elastic.dump(query=query)

        return list(doc_list)

    def upload_entry_list(self):
        """설정파일을 업로드한다."""
        entry_list = self.read_entry_list(lang=self.env.lang, column='state')

        entry_index = {}
        for item in entry_list:
            if 'entry' not in item or 'lang' not in item:
                continue

            k = '{}_{}'.format(item['entry'], item['lang'])
            entry_index[k] = item

        for f in glob('config/dict_example/*.txt'):
            f_name = f.replace('.txt', '').rsplit('/')[-1].replace('_', ' ').replace('.', ' ')
            lang = f_name.split(' ')[0].lower()

            with open(f, 'r') as fp:
                for w in fp.readlines():
                    w = w.strip()

                    if w == '':
                        continue

                    k = '{}_{}'.format(w, lang)

                    item = {
                        'entry': w,
                        'lang': lang,
                        'category': f_name,
                    }

                    if k not in entry_index:
                        entry_index[k] = item
                    else:
                        entry_index[k]['category'] = ','.join(set([entry_index[k]['category'], f_name]))

        index = 'crawler-dictionary-example-naver2-list'
        self.open_db(index)

        for doc in entry_index.values():
            doc['_id'] = str(uuid4())
            if 'document_id' in doc:
                doc['_id'] = doc['document_id']
                del doc['document_id']

            doc['state'] = ''
            self.elastic.save_document(document=doc, index=index)

        self.elastic.flush()

        return

    def is_skip(self, doc, columns):
        """ """
        text = '\t'.join([doc[col] for col in columns])
        if text in self.cache:
            self.skip += 1
            return True

        self.cache.add(text)
        return False

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--reset_list', action='store_true', default=False, help='')
        parser.add_argument('--remove_same_example', action='store_true', default=False, help='')

        parser.add_argument('--upload_entry_list', action='store_true', default=False, help='')

        return parser
