#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
from os.path import isfile

import urllib3

from nlplab.elasticsearch_utils import ElasticSearchUtils
from nlplab.minio_utils import MinioUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DataSets(object):

    def __init__(self, name=None):
        self.minio = MinioUtils()
        self.es = ElasticSearchUtils()

        self.info = {
            'movie_reviews': {
                'desc': '네이버/다음 영화 리뷰',
                'location': 'minio',
                'local_path': 'data/movie_reviews',
                'remote_path': 'movie_reviews',
                'tags': ['daum', 'naver']
            },
            'youtube/replies': {
                'desc': '유튜브 댓글',
                'location': 'minio',
                'local_path': 'data/youtube/replies',
                'remote_path': 'youtube/replies',
                'tags': ['mtd', 'news']
            }
        }

        for index in self.es.index_list():
            self.info[index] = {
                'desc': 'elasticsearch 코퍼스',
                'location': 'elasticsearch',
                'local_path': 'data/elasticsearch',
            }

        self.name = name

    def list(self):
        return [{name: self.info[name]['desc']} for name in self.info.keys()]

    def load(self, name=None, tag=None):
        meta = self.get_meta(name=name)
        if meta is None:
            return None

        if meta['location'] == 'minio':
            return self.load_minio_data(meta=meta, tag=tag)

        if meta['location'] == 'elasticsearch':
            return self.load_elasticsearch_data(meta=meta, name=name)

        return None

    def load_elasticsearch_data(self, meta, name):
        filename = '{}/{}.json.bz2'.format(meta['local_path'], name)
        if isfile(filename) is False:
            self.es.export(filename=filename, index=name)

        result = []
        with bz2.open(filename, 'rb') as fp:
            for line in fp.readlines():
                result.append(json.loads(line.decode('utf-8')))

        return result

    def load_minio_data(self, meta, tag):
        tag_list = [tag]
        if meta is None:
            tag_list = meta['tags']

        result = {}
        for tag in tag_list:
            filename = '{}/{}.json.bz2'.format(meta['local_path'], tag)

            if isfile(filename) is False:
                self.pull_minio_file(tag=tag)

            result[tag] = []
            with bz2.open(filename, 'rb') as fp:
                for line in fp.readlines():
                    result[tag].append(json.loads(line.decode('utf-8')))

        if len(result.keys()) == 1:
            return result[result.keys()[0]]

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
            local='{}/{}.json.bz2'.format(meta['local_path'], tag),
            remote='{}/{}.json.bz2'.format(meta['remote_path'], tag),
        )
        return

    def push_minio_file(self, tag, name=None):
        meta = self.get_meta(name=name)
        if meta is None:
            return

        self.minio.push(
            local='{}/{}.json.bz2'.format(meta['local_path'], tag),
            remote='{}/{}.json.bz2'.format(meta['remote_path'], tag),
        )
        return

    def batch(self, name):
        meta = self.get_meta(name=name)
        if meta is None:
            return

        for tag in meta['tags']:
            meta.push_minio_file(tag=tag)

        return


if __name__ == "__main__":
    DataSets().batch(name='movie_reviews')
