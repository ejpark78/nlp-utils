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

        self.args = None

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          + 'AppleWebKit/537.36 (KHTML, like Gecko) '
                          + 'Chrome/77.0.3865.90 Safari/537.36',
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

    def get_html(self, url):
        """ """
        headers = self.headers

        headers['Referer'] = url

        resp = requests.get(url, headers=headers, timeout=60)
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
        self.open_db(index=self.args.index)

        id_list = self.elastic.get_id_list(index=self.args.index)
        id_list = list(id_list)

        size = 1000

        start = 0
        end = size

        index = set()

        columns = self.args.columns.split(',')

        while start < len(id_list):
            doc_list = []
            self.elastic.get_by_ids(
                id_list=id_list[start:end],
                index=self.elastic.index,
                source=['document_id'] + columns,
                result=doc_list
            )

            for i, doc in enumerate(doc_list):
                if set(doc.keys()).intersection(columns) is False:
                    continue

                text = '\t'.join([doc[k] for k in columns])

                if text in index:
                    self.elastic.elastic.delete(
                        id=doc['document_id'],
                        index=self.args.index,
                    )
                    print(doc)

                index.add(text)

            if start >= len(id_list):
                break

            start = end
            end += size

            if end > len(id_list):
                end = len(id_list)

        return

    def reset_list(self):
        """ """
        self.open_db(self.args.list_index)

        query = {
            '_source': ['state', 'document_id'],
            'query': {
                'bool': {
                    'must': [
                        {
                            'match': {
                                'state': 'done'
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

            doc['state'] = ''
            self.elastic.save_document(document=doc, index=self.args.list_index)

        self.elastic.flush()

        return

    def set_as_done(self, doc):
        """ """
        doc['_id'] = doc['document_id']
        del doc['document_id']

        doc['state'] = 'done'
        doc['curl_date'] = datetime.now(self.timezone).isoformat()

        self.elastic.save_document(index=self.args.list_index, document=doc, delete=False)
        self.elastic.flush()
        return

    def read_entry_list(self):
        """설정파일을 읽어드린다."""
        self.open_db(self.args.list_index)

        query = {
            'query': {
                'bool': {
                    'must_not': [
                        {
                            'match': {
                                'state': 'done'
                            }
                        }
                    ]
                }
            }
        }

        if 'lang' in self.args and self.args.lang != '':
            query['query']['bool']['must'] = [
                {
                    'match': {
                        'lang': self.args.lang
                    }
                }
            ]

        doc_list = self.elastic.dump(query=query)

        return list(doc_list)

    def is_skip(self, doc, columns):
        """ """
        text = '\t'.join([doc[col] for col in columns])
        if text in self.cache:
            self.skip += 1
            return True

        self.cache.add(text)
        return False
