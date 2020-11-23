#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import urllib3
from minio import Minio

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class MinioUtils(object):

    def __init__(self, bucket=None, username=None, key=None, endpoint=None):
        self.bucket = bucket
        self.endpoint = endpoint
        self.username = username
        self.key = key

        if bucket is None:
            self.bucket = os.getenv('NLPLAB_DATASET_BUCKET', 'datasets')

        if username is None:
            self.username = os.getenv('NLPLAB_DATASET_USERNAME', 'k8s')

        if key is None:
            self.key = os.getenv('NLPLAB_DATASET_BUCKET_KEY', 'nlplab2020')

        if endpoint is None:
            self.endpoint = os.getenv('NLPLAB_DATASET_BUCKET_ENDPOINT', '172.19.153.41:32900')

    def push(self, local, remote):
        client = Minio(
            self.endpoint,
            access_key=self.username,
            secret_key=self.key,
            secure=False
        )

        client.fput_object(
            bucket_name=self.bucket,
            file_path=local,
            object_name=remote,
        )

        return

    def pull(self, remote, local):
        client = Minio(
            self.endpoint,
            access_key=self.username,
            secret_key=self.key,
            secure=False
        )

        client.fget_object(
            bucket_name=self.bucket,
            file_path=local,
            object_name=remote,
        )

        return
