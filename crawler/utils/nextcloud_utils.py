#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os import getenv

import jwt
import pytz
import urllib3
import webdav.client as dav_client

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NextcloudUtils(object):
    """클라우드 유틸"""

    def __init__(self):
        """ 생성자 """
        self.jwt_key = getenv('JWT_KEY', 'nlplab')

        self.timezone = pytz.timezone('Asia/Seoul')

        self.webdav_options = {
            'webdav_hostname': 'https://corpus.ncsoft.com:8080',
            'webdav_root': '/remote.php/webdav',
            'webdav_login': 'corpus_center',
            'webdav_password': 'nlplab2018',
        }

        self.client = None

        self.config = {
            'user_id': 'corpus_center',
            'user_password': 'nlplab2018'
        }

    @staticmethod
    def jwt_encode(jwt_data, jwt_key):
        """ """
        return jwt.encode(jwt_data, jwt_key).decode('utf-8')

    def open(self, access_token):
        """"""
        self.config = jwt.decode(access_token, self.jwt_key, verify=True)

        self.webdav_options['webdav_login'] = self.config['user_id']
        self.webdav_options['webdav_password'] = self.config['user_password']

        self.client = dav_client.Client(self.webdav_options)

        self.client.default_options.update({
            'SSL_VERIFYPEER': 0,
            'SSL_VERIFYHOST': 0
        })

        return self.client

    def get_cloud_corpus_tree(self, path):
        """클라우드 코퍼스 트리 구조를 조회한다."""
        result = {}

        files_list = self.client.list(path)

        for file in files_list[1:]:
            file = file.replace('/', '')

            sub_list = self.client.list(f'{path}/{file}')

            for sub_file in sub_list[1:]:
                # 마지막 / 제거
                sub_file = sub_file.replace('/', '')

                if file not in result:
                    result[file] = []

                result[file].append(sub_file)

        return result

    def get_cloud_corpus_list(self, path):
        """클라우드 코퍼스 목록 반환, 페이지 목록을 조회한다. """
        result = []

        files_list = self.client.list(path)

        for file in files_list[1:]:
            file = file.replace('/', '')

            result.append(file)

        return result
