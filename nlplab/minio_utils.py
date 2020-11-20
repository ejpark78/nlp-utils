#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import urllib3
from minio import Minio

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class MinioUtils(object):

    def __init__(self, bucket='datasets', username='k8s', key='nlplab2020', endpoint='172.19.153.41:32900'):
        self.bucket = bucket
        self.endpoint = endpoint
        self.username = username
        self.key = key

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
