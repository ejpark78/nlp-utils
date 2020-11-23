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

    def __init__(self, name):
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

        self.target = self.info[self.name]

    def load(self):
        result = {}
        for tag in self.target['tags']:
            filename = '{}/{}.json.bz2'.format(target['local_path'], tag)

            if isfile(filename) is False:
                self.pull(tag=tag)

            result[tag] = []
            with bz2.open(filename, 'rb') as fp:
                for line in fp.readlines():
                    result[tag].append(json.loads(line.decode('utf-8')))

        return result

    def pull(self, tag):
        self.minio.pull(
            local='{}/{}.json.bz2'.format(self.target['local_path'], tag),
            remote='{}/{}.json.bz2'.format(self.target['remote_path'], tag),
        )
        return

    def push(self, tag):
        self.minio.push(
            local='{}/{}.json.bz2'.format(self.target['local_path'], tag),
            remote='{}/{}.json.bz2'.format(self.target['remote_path'], tag),
        )
        return

    def batch(self):
        for tag in self.target['tags']:
            ds.push(tag=tag)
        return


if __name__ == "__main__":
    DataSets(name='movie_reviews').batch()
