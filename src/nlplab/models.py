#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tarfile
from os import getenv
from os.path import dirname

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

    def get_meta(self, name):
        if name is None:
            name = self.name

        if name is None:
            return None

        if name not in self.info.keys():
            return None

        return self.info[name]

    def pull(self, tag, name=None):
        meta = self.get_meta(name=name)
        if meta is None:
            return

        filename = '{}/{}/{}.tar.bz2'.format(self.local_home, meta['local_path'], tag)
        self.minio.pull(
            local=filename,
            remote='{}/{}/{}.tar.bz2'.format(self.remote_home, meta['remote_path'], tag),
        )

        with tarfile.open(filename, 'r:bz2') as tar:
            tar.extractall(path=dirname(filename))

        return

    def push(self, tag, name=None):
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
            self.push(name=name, tag=tag)

        return
