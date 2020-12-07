#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep

import pytz

from module.facebook.group_list import FBGroupList
from module.facebook.replies import FBReplies
from utils.selenium_utils import SeleniumUtils


class FBCrawler(object):
    """페이스북 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.params = self.init_arguments()

        self.selenium = SeleniumUtils()

    def sleep_to_login(self):
        self.selenium.open_driver()

        self.selenium.driver.get('https://m.facebook.com')
        self.selenium.driver.implicitly_wait(10)

        sleep(3200)

        return

    def batch(self):
        if self.params.login:
            self.sleep_to_login()

        if self.params.list:
            FBGroupList(params=self.params).batch()

        if self.params.reply:
            FBReplies(params=self.params).batch()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--login', action='store_true', default=False)

        parser.add_argument('--list', action='store_true', default=False)
        parser.add_argument('--reply', action='store_true', default=False)

        parser.add_argument('--overwrite', action='store_true', default=False)

        parser.add_argument('--config', default='./config/facebook/커뮤니티.json')
        parser.add_argument('--user-data', default=None)

        parser.add_argument('--use-head', action='store_false', default=True)
        parser.add_argument('--max-page', default=100, type=int)
        parser.add_argument('--max-try', default=20, type=int)

        parser.add_argument('--driver', default='/usr/bin/chromedriver')

        parser.add_argument('--host', default='https://corpus.ncsoft.com:9200')
        parser.add_argument('--auth', default='crawler:crawler2019')
        parser.add_argument('--index', default='crawler-facebook')
        parser.add_argument('--reply-index', default='crawler-facebook-reply')

        parser.add_argument('--log-path', default='log')

        return parser.parse_args()


if __name__ == '__main__':
    FBCrawler().batch()
