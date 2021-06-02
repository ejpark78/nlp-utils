#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from base64 import decodebytes
from bz2 import BZ2File
from glob import glob
from os.path import isdir

import pytz
import yaml

from crawler.facebook.parser import FacebookParser
from crawler.utils.es import ElasticSearchUtils
from crawler.utils.logger import Logger


class FacebookCore(object):

    def __init__(self, params: dict):
        super().__init__()

        self.params = params

        self.timezone = pytz.timezone('Asia/Seoul')

        self.logger = Logger()

        self.parser = FacebookParser()

        self.selenium = None

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

    def dump(self) -> None:
        self.config = self.read_config(filename=self.params['config'])

        self.es = ElasticSearchUtils(
            host=self.params['host'],
            http_auth=decodebytes(self.params['auth_encoded'].encode('utf-8')).decode('utf-8')
        )

        for index in self.config['index'].values():
            print('index: ', index)

            with BZ2File(f'{index}.json.bz2', 'wb') as fp:
                for job in self.config['jobs']:
                    query = {
                        'query': {
                            'bool': {
                                'must': [{
                                    'match': {
                                        'page': job['page']
                                    }
                                }]
                            }
                        }
                    }

                    self.es.dump_index(index=index, fp=fp, query=query, desc=job['page'])

        return
