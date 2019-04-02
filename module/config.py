#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
from os import makedirs
from os.path import dirname, abspath, isdir
from os.path import isfile


class Config(object):
    """크롤러 설정"""

    def __init__(self, job_category, job_id):
        """ 생성자 """
        status_dir = os.getenv('STATUS_DIR', 'status')

        self.debug = int(os.getenv('DEBUG', 0))

        self.headers = {
            'mobile': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                              'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                              'Version/11.0 Mobile/15A372 Safari/604.1'
            },
            'desktop': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/70.0.3538.110 Safari/537.36'
            }
        }

        job_info_filename = 'config/{category}/{job_id}/jobs.json'.format(
            category=job_category,
            job_id=job_id,
        )
        self.job_info = self.open_config(filename=job_info_filename)

        self.parsing_info = None

        parsing_info_filename = 'config/{category}/{job_id}/parsing.json'.format(
            category=job_category,
            job_id=job_id,
        )
        if isfile(parsing_info_filename):
            self.parsing_info = self.open_config(filename=parsing_info_filename)

        self.status_filename = '{status_dir}/{category}/{job_id}.json'.format(
            status_dir=status_dir,
            category=job_category,
            job_id=job_id,
        )
        self.status = self.open_config(filename=self.status_filename, create=True)

    @staticmethod
    def open_config(filename, create=False):
        """설정 파일을 읽는다."""
        from os.path import isfile

        # 없을 경우 파일 생성
        if create is True and isfile(filename) is False:
            with open(filename, 'w') as fp:
                fp.write('{}')

        # 설정 파일이 없는 경우 에러 발생
        assert isfile(filename) is True

        # 파일 로딩
        with open(filename, 'r') as fp:
            str_doc = ''.join(fp.readlines())
            result = json.loads(str_doc)

        return result

    def save_status(self):
        """현재 크롤링 위치를 저장한다."""
        # 최신 status 정보 로딩
        status = self.open_config(filename=self.status_filename, create=True)

        # 병합
        status.update(self.status)

        # 저장할 파일 위치의 경로 생성
        path = dirname(abspath(self.status_filename))
        if isdir(path) is False:
            makedirs(path)

        # 저장
        str_config = json.dumps(status, ensure_ascii=False, sort_keys=True, indent=2)
        with open(self.status_filename, 'w') as fp:
            fp.write(str_config + '\n')

        return
