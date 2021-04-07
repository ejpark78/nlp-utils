#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import tarfile
from os import getenv
from os.path import dirname, isfile

import urllib3

from corpus.utils.minio_utils import MinioUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class Models(object):

    def __init__(self, name: str = None, use_cache: bool = True):
        self.minio = MinioUtils()

        self.name = name
        self.use_cache = use_cache

        self.local_home = getenv('NLPLAB_MODEL_PATH', 'data/models')
        self.remote_home = getenv('NLPLAB_MODEL_REMOTE_HOME', 'models')

        self.meta = {}
        self.pull_meta()

    def push_meta(self) -> None:
        self.minio.push(
            local='{}/meta.json'.format(self.local_home),
            remote='{}/meta.json'.format(self.remote_home),
        )
        return

    def pull_meta(self) -> None:
        filename = '{}/meta.json'.format(self.local_home)
        if isfile(filename) is False or self.use_cache is False:
            self.minio.pull(
                local=filename,
                remote='{}/meta.json'.format(self.remote_home),
            )

        with open(filename, 'r') as fp:
            self.meta = json.load(fp=fp)

        return

    def get_info(self, name: str) -> None or dict:
        if name is None:
            name = self.name

        if name is None:
            return None

        if name not in self.meta.keys():
            return None

        return self.meta[name]

    def pull(self, tag: str, name: str = None) -> None:
        info = self.get_info(name=name)
        if info is None:
            return

        filename = '{}/{}/{}.tar.bz2'.format(self.local_home, info['local_path'], tag)
        if isfile(filename) is True and self.use_cache is True:
            return

        self.minio.pull(
            local=filename,
            remote='{}/{}/{}.tar.bz2'.format(self.remote_home, info['remote_path'], tag),
        )

        with tarfile.open(filename, 'r:bz2') as tar:
            tar.extractall(path=dirname(filename))

        return

    def push(self, tag: str, name: str = None) -> None:
        info = self.get_info(name=name)
        if info is None:
            return

        filename = '{}/{}/{}.tar.bz2'.format(self.local_home, info['local_path'], tag)
        if isfile(filename) is False:
            return

        self.minio.push(
            local=filename,
            remote='{}/{}/{}.tar.bz2'.format(self.remote_home, info['remote_path'], tag),
        )
        return

    def upload(self, name: str = None, tag: str = None) -> None:
        info = self.get_info(name=name)
        if info is None:
            return

        tag_list = [tag]
        if info is not None:
            tag_list = info['tags']

        for tag in tag_list:
            self.push(name=name, tag=tag)

        return
