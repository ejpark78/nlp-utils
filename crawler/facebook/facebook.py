#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import splitext
from time import sleep

import pytz

from .cache_utils import CacheUtils
from .group_list import FBGroupList
from .replies import FBReplies
from crawler.utils.dataset_utils import DataSetUtils


class FBCrawler(object):

    def __init__(self):
        super().__init__()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.params = self.init_arguments()

    @staticmethod
    def sleep_to_login() -> None:
        from utils import SeleniumUtils

        selenium = SeleniumUtils()

        selenium.open_driver()

        selenium.driver.get('https://m.facebook.com')
        selenium.driver.implicitly_wait(10)

        sleep(3200)
        return

    def export(self) -> None:
        alias = {
            'content': 'text',
            'user_name': 'username',
            'original_content_id': 'post_id',
        }

        columns = list(set(
            'id,reply_count,category,content,group_id,lang_code,name,original_content_id,page,page_id,'
            'id,post_id,reply_id,reply_to,text,user_name'.split(',')
        ))

        db = CacheUtils(filename=self.params.cache)

        f_name = f'{splitext(self.params.cache)[0]}.posts'
        db.export_tbl(
            filename=f'{f_name}.json.bz2',
            tbl='posts',
            db_column='id,reply_count,content',
            json_columns='content'.split(','),
            columns=columns,
            alias=alias
        )

        db.json2xlsx(filename=f_name)

        f_name = f'{splitext(self.params.cache)[0]}.replies'
        db.export_tbl(
            filename=f'{f_name}.json.bz2',
            tbl='replies',
            db_column='id,post_id,content',
            json_columns='content'.split(','),
            columns=columns,
            alias=alias
        )

        db.json2xlsx(filename=f_name)
        return

    def batch(self) -> None:
        if self.params.login:
            self.sleep_to_login()

        if self.params.account:
            FBGroupList(params=self.params).account()

        if self.params.list:
            FBGroupList(params=self.params).batch()

        if self.params.reply:
            FBReplies(params=self.params).batch()

        if self.params.upload is True:
            DataSetUtils().upload(filename=self.params.meta)

        if self.params.export is True:
            self.export()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--account', action='store_true', default=False)
        parser.add_argument('--list', action='store_true', default=False)
        parser.add_argument('--reply', action='store_true', default=False)

        parser.add_argument('--export', action='store_true', default=False, help='내보내기')
        parser.add_argument('--upload', action='store_true', default=False, help='minio 업로드')

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

        parser.add_argument('--meta', default='./data/facebook/facebook-meta.json', help='메타 파일명')

        return parser.parse_args()


if __name__ == '__main__':
    FBCrawler().batch()
