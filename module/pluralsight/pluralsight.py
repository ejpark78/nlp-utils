#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep

import pytz
import urllib3

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
            filename=self.params.filename,
            use_cache=self.params.use_cache
        )

        self.selenium = SeleniumWireUtils(
            login=self.params.login,
            headless=self.params.headless,
            user_data_path=self.params.user_data,
        )


class PluralSightCourses(PluralSightBase):

    def __init__(self, params):
        super().__init__(params=params)

    def batch(self):
        return


class PluralSightCrawler(object):

    def __init__(self):
        super().__init__()

        self.params = self.init_arguments()

    def batch(self):
        if self.params.courses:
            PluralSightCourses(params=self.params).batch()

        if self.params.login:
            sleep(10000)

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
