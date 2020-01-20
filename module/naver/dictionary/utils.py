#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import sys
from glob import glob
from os.path import isdir

import pytz
import requests
import urllib3
from bs4 import BeautifulSoup

from module.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MESSAGE = 25

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(format='%(message)s')

logger = logging.getLogger()

logger.setLevel(MESSAGE)
logger.handlers = [logging.StreamHandler(sys.stderr)]


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
        self.http_auth = 'elastic:nlplab'

        self.timezone = pytz.timezone('Asia/Seoul')

        self.elastic = None

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
