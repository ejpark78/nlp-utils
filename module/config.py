#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from datetime import datetime
from os import makedirs, getenv
from os.path import dirname, abspath, isdir, isfile

import pytz
from dateutil.relativedelta import relativedelta


class Config(object):
    """크롤러 설정"""

    def __init__(self, job_category, job_id, config=None):
        """ 생성자 """
        status_dir = getenv('STATUS_DIR', 'status')

        self.debug = int(getenv('DEBUG', 0))

        self.headers = {
            'mobile': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                              'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                              'Version/11.0 Mobile/15A372 Safari/604.1'
            },
            'desktop': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/77.0.3865.90 Safari/537.36'
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
        self.job_info = self.open_config(filename=job_info_filename)

        self.parsing_info = None

        parsing_info_filename = '{config}/parsing.json'.format(config=config)
        if isfile(parsing_info_filename):
            self.parsing_info = self.open_config(filename=parsing_info_filename)

        # 상태 저장 파일
        self.status_filename = '{status_dir}/{category}/{job_id}.json'.format(
            job_id=job_id,
            category=job_category,
            status_dir=status_dir,
        )
        self.status = self.open_config(filename=self.status_filename, job_info=self.job_info)

        return

    @staticmethod
    def open_config(filename, create=False, job_info=None):
        """설정 파일을 읽는다."""
        # 컨테이너 안에서 설정
        today = datetime.now(pytz.timezone('Asia/Seoul'))

        start_date = today + relativedelta(weeks=-1)
        end_date = today + relativedelta(years=1)

        default = {
            'trace_list': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'end': 100,
                'start': 1,
                'step': 1
            }
        }

        if job_info is not None and 'trace_list' in job_info:
            trace_list = job_info['trace_list'][0]

            for k in default['trace_list']:
                if k not in trace_list:
                    continue

                default['trace_list'][k] = trace_list[k]

        # 없을 경우 파일 생성
        if create is True and isfile(filename) is False:
            with open(filename, 'w') as fp:
                fp.write(json.dumps(default))

        # 설정 파일이 없는 경우
        if isfile(filename) is False:
            return default

            # 파일 로딩
        with open(filename, 'r') as fp:
            str_doc = ''.join(fp.readlines())
            result = json.loads(str_doc)

        return result

    def save_status(self):
        """현재 크롤링 위치를 저장한다."""
        # 최신 status 정보 로딩
        status = self.open_config(filename=self.status_filename)

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
