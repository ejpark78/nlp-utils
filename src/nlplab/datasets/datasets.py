#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
from os.path import isfile

import urllib3

from nlplab.minio_utils import MinioUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DataSets(object):

    def __init__(self, name=None):
        self.minio = MinioUtils()

        self.info = {
            'movie_reviews': {
                'desc': '네이버/다음 영화 리뷰',
                'local_path': 'data/movie_reviews',
                'remote_path': 'movie_reviews',
                'tags': ['daum', 'naver']
            },
            'youtube/replies': {
                'desc': '유튜브 댓글',
                'local_path': 'data/youtube/replies',
                'remote_path': 'youtube/replies',
                'tags': ['mtd', 'news']
            }
        }

        self.name = name

    def list(self):
        return [{name: self.info[name]['desc']} for name in self.info.keys()]

    def load(self, tag=None, name=None):
        ds = self.get_dataset_info(name=name)
        if ds is None:
            return

        tag_list = [tag]
        if tag is None:
            tag_list = ds['tags']

        result = {}
        for tag in tag_list:
            filename = '{}/{}.json.bz2'.format(ds['local_path'], tag)

            if isfile(filename) is False:
                self.pull(tag=tag)

            result[tag] = []
            with bz2.open(filename, 'rb') as fp:
                for line in fp.readlines():
                    result[tag].append(json.loads(line.decode('utf-8')))

        if len(result.keys()) == 1:
            return result[result.keys()[0]]

        return result

    def get_dataset_info(self, name):
        if name is None:
            name = self.name

        if name is None:
            return None

        if name not in self.info.keys():
            return None

        return self.info[name]

    def pull(self, tag, name=None):
        ds = self.get_dataset_info(name=name)
        if ds is None:
            return

        self.minio.pull(
            local='{}/{}.json.bz2'.format(ds['local_path'], tag),
            remote='{}/{}.json.bz2'.format(ds['remote_path'], tag),
        )
        return

    def push(self, tag, name=None):
        ds = self.get_dataset_info(name=name)
        if ds is None:
            return

        self.minio.push(
            local='{}/{}.json.bz2'.format(ds['local_path'], tag),
            remote='{}/{}.json.bz2'.format(ds['remote_path'], tag),
        )
        return

    def batch(self, name):
        ds = self.get_dataset_info(name=name)
        if ds is None:
            return

        for tag in ds['tags']:
            ds.push(tag=tag)

        return


if __name__ == "__main__":
    DataSets().batch(name='movie_reviews')
