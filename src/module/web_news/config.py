#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from datetime import datetime
from os import getenv
from os.path import isfile

import pytz


class Config(object):
    """크롤러 설정"""

    def __init__(self, job_category: str, job_id: str, config: str = None):
        self.debug = int(getenv('DEBUG', 0))

        self.headers = {
            'mobile': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                              'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                              'Version/11.0 Mobile/15A372 Safari/604.1'
            },
            'desktop': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/87.0.4280.141 Safari/537.36'
            }
        }

        # config 파일
        if config is None:
            config = 'config/{category}/{job_id}'.format(
                job_id=job_id,
                category=job_category,
            )

        # 정보
        job_info_filename = '{config}/jobs.json'.format(config=config)
        self.job_info = self.read_file(filename=job_info_filename)

        self.parsing_info = None

        parsing_info_filename = '{config}/parsing.json'.format(config=config)
        if isfile(parsing_info_filename):
            self.parsing_info = self.read_file(filename=parsing_info_filename)

        self.today = datetime.now(pytz.timezone('Asia/Seoul'))

        return

    @staticmethod
    def read_file(filename: str) -> dict or None:
        """설정 파일을 읽는다."""
        # 설정 파일이 없는 경우
        if isfile(filename) is False:
            return None

        # 파일 로딩
        with open(filename, 'r') as fp:
            str_doc = ''.join(fp.readlines())
            result = json.loads(str_doc)

        return result
