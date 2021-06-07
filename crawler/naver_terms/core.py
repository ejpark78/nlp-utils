#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from base64 import decodebytes
from bz2 import BZ2File
from os.path import splitext

import yaml

from crawler.naver_terms.corpus_lake import CorpusLake
from crawler.utils.html_parser import HtmlParser
from crawler.utils.logger import Logger


class TermsCore(object):

    def __init__(self, params: dict):
        super().__init__()

        self.params = params

        self.logger = Logger()
        self.parser = HtmlParser()

        self.headers = {
            'mobile': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/91.0.4472.77 Mobile Safari/537.36'
            },
            'desktop': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/91.0.4472.77 Safari/537.36'
            }
        }

        self.config = self.open_config(filename=self.params['config'])

        http_auth = None
        if self.params['auth_encoded']:
            http_auth = decodebytes(self.params['auth_encoded'].encode('utf-8')).decode('utf-8')

        self.config['jobs'].update({
            'host': self.params['host'],
            'index': self.params['index'],
            'list_index': self.params['list_index'],
            'http_auth': http_auth
        })

        self.job_sub_category = self.params['sub_category'].split(',') if self.params['sub_category'] != '' else []

        self.lake = None

        self.selenium = None

    @staticmethod
    def open_config(filename: str) -> dict:
        with open(filename, 'r') as fp:
            data = yaml.load(stream=fp, Loader=yaml.FullLoader)
            return data

    def dump(self) -> None:
        lake_info = {
            'type': self.params['db_type'],
            'host': self.config['jobs']['host'],
            'index': self.config['jobs']['index'],
            'bulk_size': 20,
            'auth': self.config['jobs']['http_auth'],
            'mapping': None,
            'filename': self.params['cache'],
        }

        self.lake = CorpusLake(lake_info=lake_info)

        for db_type in self.params['db_type'].split(','):
            for index in [self.config['jobs']['index'], self.config['jobs']['list_index']]:
                print('index: ', index)

                filename = f'{index}.json.bz2'
                if self.params['cache']:
                    base, _ = splitext(self.params['cache'])
                    filename = f'{base}.{index}.json.bz2'

                with BZ2File(filename, 'wb') as fp:
                    self.lake.dump_index(index=index, fp=fp, db_type=db_type)

        return

    def requests(self, url: str) -> str:
        self.selenium.driver.get(url)
        self.selenium.driver.implicitly_wait(30)

        return self.selenium.driver.page_source
