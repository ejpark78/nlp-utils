#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os import getenv

import urllib3

from nlplab.utils.minio_utils import MinioUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class Models(object):

    def __init__(self, name=None, use_cache=True):
        self.minio = MinioUtils()

        self.name = name
        self.use_cache = use_cache

        self.cache_path = getenv('NLPLAB_CACHE_PATH', 'data/models')

        self.info = {
            'kobert': {
                'desc': '네이버/다음 영화 리뷰',
                'location': 'minio',
                'local_path': 'kobert',
                'remote_path': 'kobert',
                'tags': ['daum', 'naver']
            }
        }
