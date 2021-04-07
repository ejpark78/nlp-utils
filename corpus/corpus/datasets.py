#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
from os import getenv
from os.path import basename, isfile

import urllib3

from corpus.utils.elasticsearch_utils import ElasticSearchUtils
from corpus.utils.minio_utils import MinioUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DataSets(object):

    def __init__(self, name: str = None, use_cache: bool = True):
        self.elastic = ElasticSearchUtils()
        self.minio = MinioUtils()

        self.name = name
        self.use_cache = use_cache

        self.local_home = getenv('NLPLAB_DATASET_LOCAL_HOME', 'data/datasets')
        self.remote_home = getenv('NLPLAB_DATASET_REMOTE_HOME', 'datasets')

        self.meta_path = f'{self.remote_home}/meta'

        self.meta = {}
        self.pull_meta()

    def get_info(self, name: str) -> None or dict:
        if name is None:
            name = self.name

        if name is None:
            return None

        if name not in self.meta.keys():
            return None

        return self.meta[name]

    def push_meta(self, filename: str) -> None:
        self.minio.push(
            local=f'{self.local_home}/{filename}',
            remote=f'{self.remote_home}/{filename}',
        )
        return

    def pull_meta(self) -> None:
        meta_list = self.minio.ls(path=self.meta_path)

        self.meta = {}
        for remote_meta in meta_list:
            filename = f'{self.local_home}/{basename(remote_meta)}'

            # download meta
            self.minio.pull(
                local=filename,
                remote=remote_meta,
            )

            # read meta
            with open(filename, 'r') as fp:
                content = json.load(fp=fp)

            self.meta[content['name']] = content

        return

    def pull_elastic_meta(self) -> dict:
        mappings = self.elastic.get_index_columns()

        result = {}
        for item in self.elastic.get_index_size():
            index = item['index']

            if index not in mappings:
                continue

            result[index] = {
                'name': index,
                'count': item['count'],
                'desc': 'elasticsearch 코퍼스',
                'source': self.elastic.host,
                'location': 'elasticsearch',
                'local_path': 'elasticsearch',
                'columns': mappings[index],
            }

        return result

    def load(self, name: str = None, filename: str = None, use_cache: bool = True, meta: dict = None,
             source: list = None) -> None or list:
        if meta and name in meta:
            meta = meta[name]
        else:
            meta = self.get_info(name=name)

        if meta is None:
            return None

        self.use_cache = use_cache

        if 'location' not in meta:
            if filename:
                return self.load_minio_data(meta=meta, filename=filename)

            result = []
            for x in meta['files']:
                result += self.load_minio_data(meta=meta, filename=x['name'])

            return result

        if meta['location'] == 'elasticsearch':
            return self.load_elasticsearch_data(meta=meta, name=name, source=source)

        return None

    def load_elasticsearch_data(self, meta: dict, name: str, source: list = None) -> list:
        filename = f"{self.local_home}/{meta['local_path']}/{name}.bz2"

        if isfile(filename) is False or self.use_cache is False:
            self.elastic.export(filename=filename, index=name, source=source)

        result = []
        with bz2.open(filename, 'rb') as fp:
            for line in fp.readlines():
                result.append(json.loads(line.decode('utf-8')))

        return result

    def load_minio_data(self, meta: dict, filename: str) -> list:
        local_file = f"{self.local_home}/{meta['local_path']}/{filename}"

        if isfile(local_file) is False or self.use_cache is False:
            self.pull_minio_file(filename=filename, name=meta['name'])

        result = []
        with bz2.open(local_file, 'rb') as fp:
            for line in fp.readlines():
                result.append(json.loads(line.decode('utf-8')))

        return result

    def pull_minio_file(self, filename: str, name: str = None) -> None:
        info = self.get_info(name=name)
        if info is None:
            return

        self.minio.pull(
            local=f"{self.local_home}/{info['local_path']}/{filename}",
            remote=f"{self.remote_home}/{info['remote_path']}/{filename}"
        )
        return

    def push_minio_file(self, filename: str, name: str = None) -> None:
        info = self.get_info(name=name)
        if info is None:
            return

        self.minio.push(
            local=f"{self.local_home}/{info['local_path']}/{filename}",
            remote=f"{self.remote_home}/{info['remote_path']}/{filename}"
        )
        return

    def upload(self, name: str = None, filename: str = None) -> None:
        info = self.get_info(name=name)
        if info is None:
            return

        self.push_minio_file(name=name, filename=filename)

        return

    def test(self) -> None:
        # print(self.meta)

        # data = self.load(name='daum_movie_reviews')
        # print(data)

        meta = self.pull_elastic_meta()
        # print(meta)

        data = self.load(name='crawler-naver-economy-2021', meta=meta, source='title,content'.split(','))
        # print(data)

        return


if __name__ == '__main__':
    DataSets().test()
