#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os import getenv

import urllib3
from minio import Minio

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class MinioUtils(object):

    def __init__(self, bucket=None, username=None, key=None, endpoint=None):
        self.bucket = bucket
        if bucket is None:
            self.bucket = getenv('NLPLAB_S3_BUCKET', 'datasets')

        self.username = username
        if username is None:
            self.username = getenv('NLPLAB_S3_USERNAME', 'k8s')

        self.key = key
        if key is None:
            self.key = getenv('NLPLAB_S3_BUCKET_KEY', 'nlplab2020')

        self.endpoint = endpoint
        if endpoint is None:
            self.endpoint = getenv('NLPLAB_S3_BUCKET_ENDPOINT', '172.19.153.41:32900')

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
