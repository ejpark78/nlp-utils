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

from nlplab.utils.elasticsearch_utils import ElasticSearchUtils
from nlplab.utils.minio_utils import MinioUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DataSets(object):

    def __init__(self, name=None, use_cache=True):
        self.elastic = ElasticSearchUtils()
        self.minio = MinioUtils()

        self.name = name
        self.use_cache = use_cache

        self.local_home = getenv('NLPLAB_DATASET_LOCAL_HOME', 'data/datasets')
        self.remote_home = getenv('NLPLAB_DATASET_REMOTE_HOME', 'datasets')

        self.meta_path = '{home}/meta'.format(home=self.remote_home)

        self.meta = {}
        self.pull_meta()

    def get_info(self, name):
        if name is None:
            name = self.name

        if name is None:
            return None

        if name not in self.meta.keys():
            return None

        return self.meta[name]

    def push_meta(self, filename):
        self.minio.push(
            local='{path}/{filename}'.format(path=self.local_home, filename=filename),
            remote='{path}/{filename}'.format(path=self.remote_home, filename=filename),
        )
        return

    def pull_meta(self):
        meta_list = self.minio.ls(path=self.meta_path)

        self.meta = {}
        for remote_meta in meta_list:
            filename = '{path}/{filename}'.format(
                path=self.local_home,
                filename=basename(remote_meta)
            )

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

    def pull_elastic_meta(self):
        for index in self.elastic.index_list():
            if 'corpus_process' in index:
                continue

            self.meta[index] = {
                'name': index,
                'desc': 'elasticsearch 코퍼스',
                'source': self.elastic.host,
                'local_path': 'elasticsearch',
            }

        return

    def load(self, name=None, filename=None, use_cache=True):
        meta = self.get_info(name=name)
        if meta is None:
            return None

        self.use_cache = use_cache

        if 'location' not in meta:
            return self.load_minio_data(meta=meta, filename=filename)

        if meta['location'] == 'elasticsearch':
            return self.load_elasticsearch_data(meta=meta, name=name)

        return None

    def load_elasticsearch_data(self, meta, name):
        filename = '{home}/{path}/{filename}'.format(
            home=self.local_home,
            path=meta['local_path'],
            filename=name
        )

        if isfile(filename) is False or self.use_cache is False:
            self.elastic.export(filename=filename, index=name)

        result = []
        with bz2.open(filename, 'rb') as fp:
            for line in fp.readlines():
                result.append(json.loads(line.decode('utf-8')))

        return result

    def load_minio_data(self, meta, filename):
        local_file = '{home}/{path}/{filename}'.format(
            home=self.local_home,
            path=meta['local_path'],
            filename=filename
        )

        if isfile(local_file) is False or self.use_cache is False:
            self.pull_minio_file(filename=filename, name=meta['name'])

        result = []
        with bz2.open(local_file, 'rb') as fp:
            for line in fp.readlines():
                result.append(json.loads(line.decode('utf-8')))

        return result

    def pull_minio_file(self, filename, name=None):
        info = self.get_info(name=name)
        if info is None:
            return

        self.minio.pull(
            local='{home}/{path}/{filename}'.format(
                home=self.local_home,
                path=info['local_path'],
                filename=filename
            ),
            remote='{home}/{path}/{filename}'.format(
                home=self.remote_home,
                path=info['remote_path'],
                filename=filename
            ),
        )
        return

    def push_minio_file(self, filename, name=None):
        info = self.get_info(name=name)
        if info is None:
            return

        self.minio.push(
            local='{home}/{path}/{filename}'.format(
                home=self.local_home,
                path=info['local_path'],
                filename=filename
            ),
            remote='{home}/{path}/{filename}'.format(
                home=self.remote_home,
                path=info['remote_path'],
                filename=filename
            ),
        )
        return

    def upload(self, name=None, filename=None):
        info = self.get_info(name=name)
        if info is None:
            return

        self.push_minio_file(name=name, filename=filename)

        return


if __name__ == '__main__':
    ds = DataSets()
    print(ds.meta)

    data = ds.load(name='kbsec', filename='kbsec.reports.json.bz2')
    print(data)
