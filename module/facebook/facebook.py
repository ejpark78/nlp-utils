#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os.path import splitext
from time import sleep

import pytz

from module.facebook.cache_utils import CacheUtils
from module.facebook.group_list import FBGroupList
from module.facebook.replies import FBReplies
from utils.selenium_utils import SeleniumUtils


class FBCrawler(object):

    def __init__(self):
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

    def export_posts(self):
        db = CacheUtils(filename=self.params.cache)

        column = 'id,reply_count,content'
        db.cursor.execute('SELECT {} FROM posts'.format(column))

        rows = db.cursor.fetchall()

        data = []
        for i, item in enumerate(rows):
            doc = dict(zip(column.split(','), item))

            content = json.loads(doc['content'])
            del doc['content']

            doc.update(content)

            data.append(doc)

        filename = '{}.posts'.format(splitext(self.params.cache)[0])
        db.save(filename=filename, rows=data)

        return

    def export_replies(self):
        db = CacheUtils(filename=self.params.cache)

        column = 'id,post_id,content'
        db.cursor.execute('SELECT {} FROM replies'.format(column))

        rows = db.cursor.fetchall()

        data = []
        for i, item in enumerate(rows):
            doc = dict(zip(column.split(','), item))

            content = json.loads(doc['content'])
            del doc['content']

            doc.update(content)

            data.append(doc)

        filename = '{}.replies'.format(splitext(self.params.cache)[0])
        db.save(filename=filename, rows=data)

        return

    def export(self):
        self.export_posts()
        self.export_replies()
        return

    def batch(self):
        if self.params.login:
            self.sleep_to_login()

        if self.params.list:
            FBGroupList(params=self.params).batch()

        if self.params.reply:
            FBReplies(params=self.params).batch()

        if self.params.export is True:
            self.export()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--list', action='store_true', default=False)
        parser.add_argument('--reply', action='store_true', default=False)

        parser.add_argument('--export', action='store_true', default=False, help='내보내기')

        parser.add_argument('--overwrite', action='store_true', default=False)

        parser.add_argument('--config', default='./config/facebook/커뮤니티.json')

        parser.add_argument('--login', action='store_true', default=False)
        parser.add_argument('--headless', action='store_true', default=False)
        parser.add_argument('--user-data', default=None)
        parser.add_argument('--driver', default='/usr/bin/chromedriver')

        parser.add_argument('--max-try', default=100, type=int)
        parser.add_argument('--max-page', default=10000, type=int)

        parser.add_argument('--sleep', default=10, type=float, help='sleep time')

        parser.add_argument('--host', default=None)
        parser.add_argument('--auth', default=None)
        parser.add_argument('--index', default=None)
        parser.add_argument('--reply-index', default=None)

        parser.add_argument('--log-path', default='log')

        parser.add_argument('--cache', default='./data/facebook/facebook.db', help='캐쉬명')
        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        return parser.parse_args()


if __name__ == '__main__':
    FBCrawler().batch()
