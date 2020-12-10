#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os.path import dirname

import urllib3
from nlplab.datasets import DataSets
from nlplab.utils.minio_utils import MinioUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DataSetUtils(object):

    def __init__(self):
        super().__init__()

    @staticmethod
    def upload(filename='data/kbsec/meta.json'):
        with open(filename, 'r') as fp:
            meta = json.load(fp)

        ds = DataSets()
        minio = MinioUtils()

        # upload meta
        remote_meta = '{path}/{filename}.json'.format(path=ds.meta_path, filename=meta['name'])
        minio.push(local=filename, remote=remote_meta)

        # upload datasets
        data_path = dirname(filename)
        for f in meta['files']:
            minio.push(
                local='{path}/{filename}'.format(path=data_path, filename=f['name']),
                remote='{home}/{path}/{filename}'.format(
                    home=ds.remote_home,
                    path=meta['remote_path'],
                    filename=f['name']
                ),
            )

        # ls meta
        files = minio.ls(path=ds.meta_path)
        print(files)

        files = minio.ls(path='{home}/{path}'.format(
            home=ds.remote_home,
            path=meta['remote_path']
        ))
        print(files)

        return
