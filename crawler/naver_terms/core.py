#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from base64 import decodebytes
from os import getenv

import yaml

from crawler.utils.html_parser import HtmlParser
from crawler.utils.logger import Logger


class TermsCore(object):

    def __init__(self, params: dict):
        super().__init__()

        self.params = params

        self.history = set()

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

        self.config['jobs'].update({
            'host': self.params['host'],
            'index': self.params['index'],
            'list_index': self.params['list_index'],
            'http_auth': decodebytes(self.params['auth_encoded'].encode('utf-8')).decode('utf-8')
        })

        self.job_sub_category = self.params['sub_category'].split(',') if self.params['sub_category'] != '' else []

    @staticmethod
    def open_config(filename: str) -> dict:
        with open(filename, 'r') as fp:
            data = yaml.load(stream=fp, Loader=yaml.FullLoader)
            return data
