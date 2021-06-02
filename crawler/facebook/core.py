#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from glob import glob
from os.path import isdir

import pytz
import yaml

from crawler.facebook.parser import FacebookParser
from crawler.utils.logger import Logger
from crawler.utils.selenium import SeleniumUtils


class FacebookCore(object):

    def __init__(self, params: dict):
        super().__init__()

        self.params = params

        self.timezone = pytz.timezone('Asia/Seoul')

        self.logger = Logger()

        self.parser = FacebookParser()

        self.selenium = SeleniumUtils(
            login=self.params['login'],
            headless=self.params['headless'],
            user_data_path=self.params['user_data'],
        )

        self.es = None
        self.config = None

    @staticmethod
    def read_config(filename: str) -> dict:
        file_list = filename.split(',')
        if isdir(filename) is True:
            file_list = []
            for f_name in glob(f'{filename}/*.yaml'):
                file_list.append(f_name)

        result = {'jobs': []}
        for f_name in file_list:
            with open(f_name, 'r') as fp:
                data = dict(yaml.load(stream=fp, Loader=yaml.FullLoader))

                result['jobs'] += data['jobs']
                del data['jobs']

                result.update(data)

        return result

    def create_index(self, index: str) -> None:
        if self.es is None:
            return

        if 'index_mapping' not in self.config:
            return

        mapping = self.config['index_mapping']
        self.es.create_index(
            conn=self.es.conn,
            index=index,
            mapping=mapping[index] if index in mapping else None
        )

        return
