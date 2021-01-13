#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import splitext

from module.youtube.cache_utils import CacheUtils
from module.youtube.live_chat import YoutubeLiveChat
from module.youtube.reply import YoutubeReply
from module.youtube.video_list import YoutubeVideoList
from utils.logger import Logger
from utils.selenium_wire_utils import SeleniumWireUtils
from utils.dataset_utils import DataSetUtils


class YoutubeCrawler(object):
    """유튜브 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.logger = Logger()
        self.params = self.init_arguments()

        self.selenium = SeleniumWireUtils(headless=True)

    def export(self):
        db = CacheUtils(filename=self.params.cache)

        f_name = '{filename}.channels'.format(filename=splitext(self.params.cache)[0])
        db.export_tbl(
            filename='{f_name}.json.bz2'.format(f_name=f_name),
            tbl='channels',
            db_column='id,title,video_count,data',
            json_columns='data'.split(','),
            date_columns=None,
            columns=None,
            alias=None
        )
        db.json2xlsx(filename=f_name)

        f_name = '{filename}.videos'.format(filename=splitext(self.params.cache)[0])
        db.export_tbl(
            filename='{f_name}.json.bz2'.format(f_name=f_name),
            tbl='videos',
            db_column='id,title,reply_count,tags',
            json_columns='tags'.split(','),
            date_columns=None,
            columns=None,
            alias=None
        )
        db.json2xlsx(filename=f_name)

        f_name = '{filename}.replies'.format(filename=splitext(self.params.cache)[0])
        db.export_tbl(
            filename='{f_name}.json.bz2'.format(f_name=f_name),
            tbl='reply',
            db_column='id,video_id,video_title,data',
            json_columns='data,voteCount'.split(','),
            date_columns=None,
            columns='id,video_id,title,reply_id,username,like,reply,text'.split(','),
            alias={
                'authorText.simpleText': 'username',
                'likeCount': 'like',
                'replyCount': 'reply',
                'commentId': 'reply_id',
                'video_title': 'title',
                'contentText.runs.:.text': 'text',
            }
        )
        db.json2xlsx(filename=f_name)

        return

    def batch(self):
        if self.params.videos is True:
            YoutubeVideoList(params=self.params).batch()

        if self.params.reply is True:
            YoutubeReply(params=self.params).batch()

        if self.params.live_chat is True:
            YoutubeLiveChat(params=self.params).batch()

        if self.params.upload is True:
            DataSetUtils().upload(filename=self.params.meta)

        if self.params.export is True:
            self.export()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--videos', action='store_true', default=False, help='비디오 목록 조회')
        parser.add_argument('--reply', action='store_true', default=False, help='댓글 조회')
        parser.add_argument('--live-chat', action='store_true', default=False, help='라이브챗 조회')

        parser.add_argument('--export', action='store_true', default=False, help='내보내기')
        parser.add_argument('--upload', action='store_true', default=False, help='minio 업로드')

        parser.add_argument('--cache', default='./data/youtube/mtd.db', help='파일명')
        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--max-scroll', default=5, type=int, help='최대 스크롤수')

        parser.add_argument('--sleep', default=5, type=float, help='sleep time')

        parser.add_argument('--template', default='./config/youtube/template.json', help='channel template')
        parser.add_argument('--channel-list', default='./config/youtube/mtd.json', help='channel 목록')

        parser.add_argument('--login', action='store_true', default=False)
        parser.add_argument('--headless', action='store_true', default=False)
        parser.add_argument('--user-data', default=None)

        parser.add_argument('--meta', default='./data/youtube/mtd-meta.json', help='메타 파일명')

        return parser.parse_args()


if __name__ == '__main__':
    YoutubeCrawler().batch()
