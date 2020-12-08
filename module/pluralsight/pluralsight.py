#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
from os import makedirs, rename
from os.path import isfile, isdir, dirname
from time import sleep

import pytz
import requests
import urllib3
from tqdm import tqdm

from module.pluralsight.cache_utils import CacheUtils
from utils.logger import Logger
from utils.selenium_wire_utils import SeleniumWireUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class PluralSightBase(object):

    def __init__(self, params):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.params = params

        self.db = CacheUtils(
            filename=self.params.cache,
            use_cache=self.params.use_cache
        )

        self.selenium = SeleniumWireUtils(
            login=self.params.login,
            headless=self.params.headless,
            user_data_path=self.params.user_data,
        )

    def download_file(self, url, filename):
        if isfile(filename) is True:
            self.logger.log({
                'level': 'MESSAGE',
                'message': '파일이 이미 존재함',
                'url': url,
                'filename': filename,
            })
            return

        self.logger.log({
            'level': 'MESSAGE',
            'message': '파일 다운로드',
            'url': url,
            'filename': filename,
        })

        resp = requests.get(
            url=url,
            timeout=6000,
            verify=False,
            stream=True,
            headers=self.selenium.headers,
            allow_redirects=True,
        )

        if resp.status_code // 100 != 2:
            self.logger.error(msg={
                'error': 'error: {}'.format(resp.text)
            })

        total_size = int(resp.headers.get('content-length', 0))
        self.logger.log(msg={
            'size': 'size: {:,}'.format(total_size)
        })

        path = dirname(filename)
        if isdir(path) is False:
            makedirs(path)

        wrote = 0
        block_size = 1024

        with open(filename + '.parted', 'wb') as fp:
            p_bar = tqdm(
                resp.iter_content(block_size),
                total=math.ceil(total_size // block_size), unit='KB',
                unit_scale=True
            )

            for data in p_bar:
                wrote = wrote + len(data)
                fp.write(data)

        rename(filename + '.parted', filename)
        return


class PluralSightCourses(PluralSightBase):

    def __init__(self, params):
        super().__init__(params=params)

    def batch(self):
        self.selenium.open(url='https://app.pluralsight.com/library/')
        sleep(self.params.sleep)

        return


class PluralSightCrawler(object):

    def __init__(self):
        super().__init__()

        self.params = self.init_arguments()

    def batch(self):
        if self.params.login:
            PluralSightCourses(params=self.params).selenium.open(url='https://app.pluralsight.com/library/')
            sleep(10000)

        if self.params.courses:
            PluralSightCourses(params=self.params).batch()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--courses', action='store_true', default=False)

        parser.add_argument('--login', action='store_true', default=False)
        parser.add_argument('--headless', action='store_true', default=False)

        parser.add_argument('--user-data', default='./cache/selenium/pluralsight')

        parser.add_argument('--filename', default='data/pluralsight/cache.db', help='파일명')

        parser.add_argument('--sleep', default=15, type=float, help='sleep time')

        return parser.parse_args()


if __name__ == '__main__':
    PluralSightCrawler().batch()
