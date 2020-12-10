#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
from os import getenv
from os.path import isfile

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

    def push_meta(self):
        self.minio.push(
            local='{}/meta.json'.format(self.local_home),
            remote='{}/meta.json'.format(self.remote_home),
        )
        return

    def pull_meta(self):
        filename = '{}/meta.json'.format(self.local_home)
        if isfile(filename) is False or self.use_cache is False:
            self.minio.pull(
                local=filename,
                remote='{}/meta.json'.format(self.remote_home),
            )

        with open(filename, 'r') as fp:
            self.meta = json.load(fp=fp)

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

    def load(self, name=None, tag=None, use_cache=True):
        meta = self.get_info(name=name)
        if meta is None:
            return None

        self.use_cache = use_cache

        if meta['location'] == 'minio':
            return self.load_minio_data(meta=meta, tag=tag)

        if meta['location'] == 'elasticsearch':
            return self.load_elasticsearch_data(meta=meta, name=name)

        return None

    def load_elasticsearch_data(self, meta, name):
        filename = '{}/{}/{}.json.bz2'.format(self.local_home, meta['local_path'], name)
        if isfile(filename) is False or self.use_cache is False:
            self.elastic.export(filename=filename, index=name)

        result = []
        with bz2.open(filename, 'rb') as fp:
            for line in fp.readlines():
                result.append(json.loads(line.decode('utf-8')))

        return result

    def load_minio_data(self, meta, tag):
        tag_list = []
        if tag is not None:
            tag_list = [tag]

        if len(tag_list) == 0 and meta is not None:
            tag_list = meta['tags']

        result = {}
        if len(tag_list) == 0:
            return result

        for tag_nam in tag_list:
            filename = '{}/{}/{}.json.bz2'.format(self.local_home, meta['local_path'], tag_nam)

            if isfile(filename) is False or self.use_cache is False:
                self.pull_minio_file(tag=tag)

            result[tag_nam] = []
            with bz2.open(filename, 'rb') as fp:
                for line in fp.readlines():
                    result[tag_nam].append(json.loads(line.decode('utf-8')))

        if tag is not None:
            return result[list(result.keys())[0]]

        return result

    def get_info(self, name):
        if name is None:
            name = self.name

        if name is None:
            return None

        if name not in self.meta.keys():
            return None

        return self.meta[name]

    def pull_minio_file(self, tag, name=None):
        info = self.get_info(name=name)
        if info is None:
            return

        self.minio.pull(
            local='{}/{}/{}.json.bz2'.format(self.local_home, info['local_path'], tag),
            remote='{}/{}/{}.json.bz2'.format(self.remote_home, info['remote_path'], tag),
        )
        return

    def push_minio_file(self, tag, name=None):
        info = self.get_info(name=name)
        if info is None:
            return

        self.minio.push(
            local='{}/{}/{}.json.bz2'.format(self.local_home, info['local_path'], tag),
            remote='{}/{}/{}.json.bz2'.format(self.remote_home, info['remote_path'], tag),
        )
        return

    def upload(self, name=None, tag=None):
        info = self.get_info(name=name)
        if info is None:
            return

        tag_list = [tag]
        if info is not None:
            tag_list = info['tags']

        for tag in tag_list:
            self.push_minio_file(name=name, tag=tag)

        return
