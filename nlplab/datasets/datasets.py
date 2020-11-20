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


class datasets(object):

    def __init__(self, name):
        self.minio = MinioUtils()

        self.name = name

        self.path = {
            'local': 'data/{}'.format(name),
            'remote': name
        }

        self.tags = {
            'movie_reviews': ['daum', 'naver']
        }

    def load(self):
        result = {}
        for tag in self.tags[self.name]:
            filename = '{}/{}.json.bz2'.format(self.path['local'], tag)

            if isfile(filename) is False:
                self.pull(tag=tag)

            result[tag] = []
            with bz2.open(filename, 'rb') as fp:
                for line in fp.readlines():
                    result[tag].append(json.loads(line.decode('utf-8')))

        return result

    def pull(self, tag):
        self.minio.pull(
            local='{}/{}.json.bz2'.format(self.path['local'], tag),
            remote='{}/{}.json.bz2'.format(self.path['remote'], tag),
        )
        return

    def push(self, tag):
        self.minio.push(
            local='{}/{}.json.bz2'.format(self.path['local'], tag),
            remote='{}/{}.json.bz2'.format(self.path['remote'], tag),
        )
        return


if __name__ == "__main__":
    datasets().push()
