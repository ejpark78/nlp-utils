#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

import pandas as pd

from module.utils.logger import Logger
from module.utils.selenium_wire_utils import SeleniumWireUtils
from module.youtube.cache_utils import CacheUtils
from module.youtube.reply import YoutubeReply
from module.youtube.video_list import YoutubeVideoList


class YoutubeCrawler(object):
    """유튜브 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.logger = Logger()

        self.selenium = SeleniumWireUtils(headless=True)

        self.params = self.init_arguments()

    def export_channels(self):
        db = CacheUtils(filename=self.params.filename)

        column = 'id,title,video_count,data'
        db.cursor.execute('SELECT {} FROM channels'.format(column))

        rows = db.cursor.fetchall()

        data = []
        channels = {}
        for i, item in enumerate(rows):
            r = dict(zip(column.split(','), item))
            tags = json.loads(r['data'])
            del r['data']

            channels[item[0]] = {'channels.{}'.format(k): tags[k] for k in tags.keys()}

            r.update(channels[item[0]])
            data.append(r)

        pd.DataFrame(data).to_excel('data/youtube-channels.xlsx')

        return channels

    def export_videos(self, channels):
        db = CacheUtils(filename=self.params.filename)

        column = 'id,title,reply_count,tags'
        db.cursor.execute('SELECT {} FROM videos'.format(column))

        rows = db.cursor.fetchall()

        data = []
        videos = {}
        for i, item in enumerate(rows):
            r = dict(zip(column.split(','), item))
            tags = json.loads(r['tags'])
            del r['tags']

            videos[item[0]] = {'videos.{}'.format(k): tags[k] for k in tags.keys()}

            r.update(tags)

            if item[1] in channels:
                r.update(channels[item[1]])

            data.append(r)

        pd.DataFrame(data).to_excel('data/youtube-videos.xlsx')

        return videos

    def export_reply(self, videos):
        db = CacheUtils(filename=self.params.filename)

        column = 'id,video_id,video_title,data'
        db.cursor.execute('SELECT {} FROM reply'.format(column))

        rows = db.cursor.fetchall()

        data = []
        for i, item in enumerate(rows):
            r = dict(zip(column.split(','), item))

            reply = json.loads(r['data'])
            del r['data']

            r['username'] = reply['authorText']['simpleText']
            r['contentText'] = reply['contentText']['runs'][0]['text']
            r['isLiked'] = reply['isLiked']
            r['likeCount'] = reply['likeCount']

            r['replyCount'] = 0
            if 'replyCount' in reply:
                r['replyCount'] = reply['replyCount']

            if item[1] in videos:
                r.update(videos[item[1]])

            data.append(r)

        pd.DataFrame(data).to_excel('data/youtube-replies.xlsx')

        return

    def export(self):
        channels = self.export_channels()

        videos = self.export_videos(channels=channels)

        self.export_reply(videos=videos)
        return

    def test(self):
        db = CacheUtils(filename=self.params.filename)

        db.cursor.execute('SELECT id FROM videos WHERE data NOT LIKE ?', ('%삼프로tv%',))

        videos = [x[0] for x in db.cursor.fetchall()]

        sql = 'DELETE FROM reply WHERE video_id=?'
        for v_id in videos:
            db.cursor.execute(sql, (v_id,))

        db.conn.commit()

        return

    def batch(self):
        if self.params.test is True:
            self.test()

        if self.params.videos is True:
            YoutubeVideoList(params=self.params).batch()

        if self.params.reply is True:
            YoutubeReply(params=self.params).batch()

        if self.params.export is True:
            self.export()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--test', action='store_true', default=False, help='테스트')
        parser.add_argument('--videos', action='store_true', default=False, help='비디오 목록 조회')
        parser.add_argument('--reply', action='store_true', default=False, help='댓글 조회')

        parser.add_argument('--export', action='store_true', default=False, help='내보내기')

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--filename', default='./data/youtube/mtd.db', help='파일명')
        parser.add_argument('--max-scroll', default=5, type=int, help='최대 스크롤수')

        parser.add_argument('--sleep', default=5, type=float, help='sleep time')

        parser.add_argument('--template', default='./config/youtube/template.json', help='channel template')
        parser.add_argument('--channel-list', default='./config/youtube/mtd.json', help='channel 목록')

        return parser.parse_args()


if __name__ == '__main__':
    YoutubeCrawler().batch()
