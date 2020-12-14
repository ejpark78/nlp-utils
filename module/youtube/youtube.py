#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
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

    def export_channels(self):
        db = CacheUtils(filename=self.params.cache)

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

        filename = '{}.channels'.format(splitext(self.params.cache)[0])
        db.save(filename=filename, rows=data)

        return channels

    def export_videos(self, channels):
        db = CacheUtils(filename=self.params.cache)

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

        filename = '{}.videos'.format(splitext(self.params.cache)[0])
        db.save(filename=filename, rows=data)

        return videos

    def export_reply(self, videos):
        db = CacheUtils(filename=self.params.cache)

        column = 'id,video_id,video_title,data'
        db.cursor.execute('SELECT {} FROM reply'.format(column))

        rows = db.cursor.fetchall()

        data = []
        for i, item in enumerate(rows):
            r = dict(zip(column.split(','), item))

            reply = json.loads(r['data'])
            del r['data']

            if 'runs' not in reply['contentText']:
                print(reply['contentText'])
                continue

            if 'authorText' not in reply:
                print(reply)
                continue

            r['username'] = reply['authorText']['simpleText']
            r['contentText'] = reply['contentText']['runs'][0]['text']
            r['isLiked'] = reply['isLiked']
            r['likeCount'] = reply['likeCount']

            r['replyCount'] = 0
            if 'replyCount' in reply:
                r['replyCount'] = reply['replyCount']

            # if item[1] in videos:
            #     r.update(videos[item[1]])

            data.append(r)

        filename = '{}.replies'.format(splitext(self.params.cache)[0])
        db.save(filename=filename, rows=data)

        return

    def export(self):
        channels = self.export_channels()

        videos = self.export_videos(channels=channels)

        self.export_reply(videos=videos)
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
