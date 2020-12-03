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

        self.cache_path = getenv('NLPLAB_CACHE_PATH', 'data/datasets')

        self.info = {
            'movie_reviews': {
                'desc': '네이버/다음 영화 리뷰',
                'location': 'minio',
                'local_path': 'movie_reviews',
                'remote_path': 'movie_reviews',
                'tags': ['daum', 'naver']
            },
            'youtube/replies': {
                'desc': '유튜브 댓글',
                'location': 'minio',
                'local_path': 'youtube/replies',
                'remote_path': 'youtube/replies',
                'tags': ['mtd', 'news']
            }
        }

        for index in self.elastic.index_list():
            if 'corpus_process' in index:
                continue

            self.info[index] = {
                'desc': 'elasticsearch 코퍼스',
                'location': 'elasticsearch',
                'local_path': 'elasticsearch',
            }

    def list(self):
        return [{name: self.info[name]['desc']} for name in self.info.keys()]

    def load(self, name=None, tag=None, use_cache=True):
        meta = self.get_meta(name=name)
        if meta is None:
            return None

        self.use_cache = use_cache

        if meta['location'] == 'minio':
            return self.load_minio_data(meta=meta, tag=tag)

        if meta['location'] == 'elasticsearch':
            return self.load_elasticsearch_data(meta=meta, name=name)

        return None

    def load_elasticsearch_data(self, meta, name):
        filename = '{}/{}/{}.json.bz2'.format(self.cache_path, meta['local_path'], name)
        if isfile(filename) is False or self.use_cache is False:
            self.elastic.export(filename=filename, index=name)

        result = []
        with bz2.open(filename, 'rb') as fp:
            for line in fp.readlines():
                result.append(json.loads(line.decode('utf-8')))

        return result

    def load_minio_data(self, meta, tag):
        tag_list = [tag]
        if meta is not None:
            tag_list = meta['tags']

        result = {}
        for tag in tag_list:
            filename = '{}/{}/{}.json.bz2'.format(self.cache_path, meta['local_path'], tag)

            if isfile(filename) is False or self.use_cache is False:
                self.pull_minio_file(tag=tag)

            result[tag] = []
            with bz2.open(filename, 'rb') as fp:
                for line in fp.readlines():
                    result[tag].append(json.loads(line.decode('utf-8')))

        if len(result.keys()) == 1:
            return result[list(result.keys())[0]]

        return result

    def get_meta(self, name):
        if name is None:
            name = self.name

        if name is None:
            return None

        if name not in self.info.keys():
            return None

        return self.info[name]

    def pull_minio_file(self, tag, name=None):
        meta = self.get_meta(name=name)
        if meta is None:
            return

        self.minio.pull(
            local='{}/{}/{}.json.bz2'.format(self.cache_path, meta['local_path'], tag),
            remote='{}/{}.json.bz2'.format(meta['remote_path'], tag),
        )
        return

    def push_minio_file(self, tag, name=None):
        meta = self.get_meta(name=name)
        if meta is None:
            return

        self.minio.push(
            local='{}/{}/{}.json.bz2'.format(self.cache_path, meta['local_path'], tag),
            remote='{}/{}.json.bz2'.format(meta['remote_path'], tag),
        )
        return

    def upload(self, name=None, tag=None):
        meta = self.get_meta(name=name)
        if meta is None:
            return

        tag_list = [tag]
        if meta is not None:
            tag_list = meta['tags']

        for tag in tag_list:
            self.push_minio_file(name=name, tag=tag)

        return
