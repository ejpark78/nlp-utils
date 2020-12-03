#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
from os import getenv
from os.path import isfile
import tarfile

import urllib3

from nlplab.utils.minio_utils import MinioUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class Models(object):

    def __init__(self, name=None, use_cache=True):
        self.minio = MinioUtils()

        self.name = name
        self.use_cache = use_cache

        self.local_home = getenv('NLPLAB_MODEL_PATH', 'data/models')
        self.remote_home = getenv('NLPLAB_MODEL_REMOTE_HOME', 'models')

        self.info = {
            'bert': {
                'desc': '버트 모델',
                'location': 'minio',
                'local_path': 'bert',
                'remote_path': 'bert',
                'tags': [
                    '002_bert_morp_tensorflow',
                    '004_bert_eojeol_tensorflow'
                ]
            }
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

        return None

    def load_minio_data(self, meta, tag):
        tag_list = [tag]
        if meta is not None:
            tag_list = meta['tags']

        result = {}
        for tag in tag_list:
            filename = '{}/{}/{}.tar.bz2'.format(self.local_home, meta['local_path'], tag)

            if isfile(filename) is False or self.use_cache is False:
                self.pull_minio_file(tag=tag)

            result[tag] = []
            with tarfile.open(filename, 'r:bz2') as tar:
                tar.extractall(path=self.local_home)

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
            local='{}/{}/{}.tar.bz2'.format(self.local_home, meta['local_path'], tag),
            remote='{}/{}/{}.tar.bz2'.format(self.remote_home, meta['remote_path'], tag),
        )
        return

    def push_minio_file(self, tag, name=None):
        meta = self.get_meta(name=name)
        if meta is None:
            return

        self.minio.push(
            local='{}/{}/{}.tar.bz2'.format(self.local_home, meta['local_path'], tag),
            remote='{}/{}/{}.tar.bz2'.format(self.remote_home, meta['remote_path'], tag),
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
