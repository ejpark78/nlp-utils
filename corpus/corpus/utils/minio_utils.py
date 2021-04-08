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

    def __init__(self, bucket: str = None, encoded_auth: str = None, endpoint: str = None):
        self.bucket = bucket
        if bucket is None:
            self.bucket = getenv('MINIO_BUCKET', 'nlplab')

        if encoded_auth is None:
            encoded_auth = getenv('MINIO_ENCODED_AUTH', 'azhzOm5scGxhYjIwMjA=')

        self.username, self.key = decodebytes(encoded_auth.encode('utf-8')).decode('utf-8').split(':')

        # nlp-utils: 172.19.153.41 nlp-s3.cloud.ncsoft.com
        self.endpoint = endpoint
        if endpoint is None:
            self.endpoint = getenv('MINIO_ENDPOINT', 'nlp-s3.cloud.ncsoft.com:32900')

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
