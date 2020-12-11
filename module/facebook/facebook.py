#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import splitext
from time import sleep

import pytz

from module.facebook.cache_utils import CacheUtils
from module.facebook.group_list import FBGroupList
from module.facebook.replies import FBReplies
from utils.dataset_utils import DataSetUtils


class FBCrawler(object):

    def __init__(self):
        super().__init__()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.params = self.init_arguments()

    @staticmethod
    def sleep_to_login():
        from utils.selenium_utils import SeleniumUtils

        selenium = SeleniumUtils()

        selenium.open_driver()

        selenium.driver.get('https://m.facebook.com')
        selenium.driver.implicitly_wait(10)

        sleep(3200)
        return

    def export(self):
        columns = 'id,reply_count,category,content,group_id,lang_code,name,original_content_id,page,page_id'.split(',')
        columns += 'id,post_id,reply_id,reply_to,text,user_name'.split(',')

        columns = list(set(columns))

        # stop_columns = 'page_insights,tagged_locations,throwback_story_fbid,reactions,top_level_post_id,actor_id,' \
        #                'qid,content_owner_id_new,photo_id,attached_story_attachment_style,action_source,' \
        #                'attached_story_attachment_style,story_location,original_content_owner_id,filter,tn,' \
        #                'tl_objid,src,story_attachment_style,html_content,raw_html,linkdata,url,feedback_source,' \
        #                'feedback_target,document_id,mf_story_key,share_id,state,tds_flgs,data-uniqueid,' \
        #                'photo_attachments_list'.split(',')
        #
        # stop_columns = list(set(stop_columns))

        db = CacheUtils(filename=self.params.cache)

        db.export_tbl(
            filename='{filename}.{tbl}.json.bz2'.format(
                tbl='posts',
                filename=splitext(self.params.cache)[0]
            ),
            tbl='posts',
            column='id,reply_count,content',
            json_column='content',
            columns=columns
        )

        db.export_tbl(
            filename='{filename}.{tbl}.json.bz2'.format(
                tbl='posts',
                filename=splitext(self.params.cache)[0]
            ),
            tbl='replies',
            column='id,post_id,content',
            json_column='content',
            columns=columns
        )
        return

    def batch(self):
        if self.params.login:
            self.sleep_to_login()

        if self.params.account:
            FBGroupList(params=self.params).account()

        if self.params.list:
            FBGroupList(params=self.params).batch()

        if self.params.reply:
            FBReplies(params=self.params).batch()

        if self.params.upload is True:
            DataSetUtils().upload(filename='data/facebook/meta.json')

        if self.params.export is True:
            self.export()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
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

        return parser.parse_args()


if __name__ == '__main__':
    FBCrawler().batch()
