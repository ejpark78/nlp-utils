#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os import getenv

import urllib3
from minio import Minio
from base64 import decodebytes

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class MinioUtils(object):

    def __init__(self, bucket: str = None, username: str = None, key: str = None, endpoint: str = None):
        self.bucket = bucket
        if bucket is None:
            self.bucket = getenv('NLPLAB_S3_BUCKET', 'nlplab')

        self.username = username
        if username is None:
            self.username = getenv('NLPLAB_S3_USERNAME', 'k8s')

        self.key = key
        if key is None:
            encoded_key = getenv('NLPLAB_S3_BUCKET_KEY_ENCODED', 'bmxwbGFiMjAyMA==')
            self.key = decodebytes(encoded_key.encode('utf-8')).decode('utf-8')

        # nlp-utils: 172.19.153.41
        self.endpoint = endpoint
        if endpoint is None:
            self.endpoint = getenv('NLPLAB_S3_BUCKET_ENDPOINT', '172.19.153.41:32900')

    def push(self, local: str, remote: str) -> None:
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

    def pull(self, remote: str, local: str) -> None:
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

    def ls(self, path: str) -> list:
        client = Minio(
            self.endpoint,
            access_key=self.username,
            secret_key=self.key,
            secure=False
        )

        objects = client.list_objects(
            prefix=path,
            recursive=True,
            bucket_name=self.bucket,
        )

        return [x.object_name for x in objects]
