#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from time import sleep

import pandas as pd

from module.utils.logger import Logger
from module.utils.selenium_wire_utils import SeleniumWireUtils
from module.youtube.cache_utils import CacheUtils


class YoutubeCrawler(object):
    """유튜브 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.params = self.init_arguments()

        self.env = None

        self.logger = Logger()

        self.home_path = 'data/youtube'
        self.data_path = self.home_path

        self.selenium = SeleniumWireUtils(headless=True)

        self.max_scroll = self.params.max_scroll

        self.db = CacheUtils(filename=self.params.filename)
        self.db.use_cache = self.params.use_cache

        self.sleep_time = 5

    def get_playlist(self, url, meta, tab_name='videos'):
        self.selenium.open(url=url, resp_url_path=None, wait_for_path=None)

        init_data = self.selenium.driver.execute_script('return window["ytInitialData"]')
        tabs = init_data['contents']['twoColumnBrowseResultsRenderer']['tabs']

        tab = tabs[2]
        if tab_name == 'videos':
            tab = tabs[1]

        result = \
            tab['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0][
                'gridRenderer']['items']

        self.selenium.scroll(count=self.max_scroll, meta=meta)

        for x in self.selenium.get_requests(resp_url_path='/browse_ajax'):
            result += x.data[1]['response']['continuationContents']['gridContinuation']['items']

        if tab_name == 'videos':
            return [x['gridVideoRenderer'] for x in result]

        return [x['gridPlaylistRenderer'] for x in result]

    def get_video_list(self):
        url_list = [{
            'lang': 'ko',
            'tag': 'economy',
            'title': '삼프로TV_경제의신과함께',
            'videos': 'https://www.youtube.com/c/%EC%82%BC%ED%94%84%EB%A1%9Ctv/videos?view=0',
            'playlist': 'https://www.youtube.com/c/%EC%82%BC%ED%94%84%EB%A1%9Ctv/playlists?view=1&flow=grid',
        }, {
            'lang': 'en',
            'tag': 'L2',
            'title': 'Clobberstomp',
            'videos': 'https://www.youtube.com/c/Clobberstomped/videos?view=0&sort=dd&shelf_id=0',
            'playlist': 'https://www.youtube.com/c/Clobberstomped/playlists?view=1&flow=grid',
        }, {
            'lang': 'cn',
            'tag': 'L2',
            'title': 'WuKong国人大联盟L2Classic.club天堂2欧服怀旧',
            'videos': 'https://www.youtube.com/channel/UCKwmshJy5DTFjXjYe7STsOA/videos',
            'playlist': '',
        }, {
            'lang': 'vi',
            'tag': 'L2',
            'title': 'Neton - Chuyên công nghệ',
            'videos': 'https://www.youtube.com/channel/UCcRsvqTKNQ8JLPTmHNyqrGw/videos',
            'playlist': '',
        }, {
            'lang': 'th',
            'tag': 'L2',
            'title': 'Lineage2 Revolution Thailand - Official',
            'videos': 'https://www.youtube.com/channel/UCdYyqdH0oc3RUt9pt1ld9JA/videos',
            'playlist': '',
        }]

        for item in url_list:
            videos = self.get_playlist(url=item['videos'], tab_name='videos', meta=item)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '동영상 목록 조회',
                'count': len(videos),
                **item
            })

            for data in videos:
                self.db.save_videos(
                    v_id=data['videoId'],
                    title=data['title']['runs'][0]['text'],
                    data=data,
                    tags=item,
                )

            sleep(self.sleep_time)

        return

    def get_total_reply_count(self):
        self.selenium.scroll(count=3, meta={})

        for x in self.selenium.get_requests(resp_url_path='/comment_service_ajax'):
            if 'itemSectionContinuation' not in x.data['response']['continuationContents']:
                continue

            resp_item = x.data['response']['continuationContents']['itemSectionContinuation']
            if 'header' not in resp_item.keys():
                continue

            if 'commentsCount' not in resp_item['header']['commentsHeaderRenderer']:
                continue

            total_text = resp_item['header']['commentsHeaderRenderer']['commentsCount']['simpleText']
            if '천' in total_text:
                total = float(total_text.replace('천', '')) * 1000
            elif '만' in total_text:
                total = float(total_text.replace('만', '')) * 10000
            else:
                total = float(total_text)

            total = round(total, 0)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '댓글수',
                'total': total
            })

            return total

        return -1

    def get_more_reply(self, v_id, title, meta, total, reply_sum=0, max_try=500, max_zero_count=10):
        if max_try < 0:
            return

        if total > 10:
            scroll_count = self.max_scroll if total > 20 else 3
            self.selenium.scroll(count=scroll_count, meta=meta)

        contents = []
        for x in self.selenium.get_requests(resp_url_path='/comment_service_ajax'):
            if 'itemSectionContinuation' not in x.data['response']['continuationContents']:
                continue

            resp_item = x.data['response']['continuationContents']['itemSectionContinuation']
            if 'contents' not in resp_item:
                continue

            contents += resp_item['contents']

        replies = [x['commentThreadRenderer']['comment']['commentRenderer'] for x in contents]
        for data in replies:
            self.db.save_reply(
                c_id=data['commentId'],
                video_id=v_id,
                video_title=title,
                data=data
            )

        reply_sum += len(replies)

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '댓글 조회 계속',
            'count': len(replies),
            'reply_sum': reply_sum,
            'max_try': max_try,
            'total': total,
        })

        if len(replies) == 0:
            max_zero_count -= 1

            if max_zero_count < 0 or total - reply_sum < 50:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '댓글 조회 중지',
                    'max_try': max_try,
                    'count': len(replies),
                    'total': total,
                    'reply_sum': reply_sum,
                    'max_zero_count': max_zero_count,
                })

                return reply_sum
        else:
            max_zero_count = 10

        if reply_sum < total:
            del self.selenium.driver.requests

            self.get_more_reply(
                v_id=v_id,
                title=title,
                meta=meta,
                total=total,
                max_try=max_try - 1,
                reply_sum=reply_sum,
                max_zero_count=max_zero_count,
            )

        return reply_sum

    def get_reply(self):
        sql = 'SELECT id, title FROM videos WHERE reply_count < 0'
        self.db.cursor.execute(sql)

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            v_id = item[0]
            title = item[1]

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '댓글 조회',
                'video id': v_id,
                'title': title,
                'position': i,
                'size': len(rows)
            })

            url = 'https://www.youtube.com/watch?v={v_id}'.format(v_id=v_id)
            self.selenium.open(
                url=url,
                resp_url_path=None,
                wait_for_path=None
            )

            total = self.get_total_reply_count()
            if total == 0:
                self.db.update_reply_count(v_id=v_id, count=0)
                sleep(self.sleep_time)
                continue

            reply_count = self.get_more_reply(
                v_id=v_id,
                title=title,
                meta={'title': title, 'position': i},
                total=total
            )

            self.db.update_reply_count(v_id=v_id, count=reply_count)
            sleep(self.sleep_time)

        return

    def get_live_chat(self):
        sql = 'SELECT id, title FROM videos'
        self.db.cursor.execute(sql)

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            v_id = item[0]
            title = item[1]

            v_id = 's5kHF08Sqi4'

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '라이브 채팅 조회',
                'video id': v_id,
                'title': title,
                'position': i,
                'size': len(rows)
            })

            url = 'https://www.youtube.com/watch?v={v_id}'.format(v_id=v_id)
            self.selenium.open(
                url=url,
                resp_url_path=None,
                wait_for_path=None
            )

            init_data = self.selenium.driver.execute_script('return window["ytInitialData"]')

            for x in self.selenium.get_requests(resp_url_path='/get_live_chat_replay'):
                pass

        return

    def get_caption(self):
        return

    def export(self):
        # video
        column = 'id,title,reply_count,tags'
        self.db.cursor.execute('SELECT {} FROM videos'.format(column))

        rows = self.db.cursor.fetchall()

        meta = {}

        data = []
        for i, item in enumerate(rows):
            r = dict(zip(column.split(','), item))
            tags = json.loads(r['tags'])
            del r['tags']

            r.update(tags)
            data.append(r)

            meta[item[0]] = tags

        pd.DataFrame(data).to_excel('youtube-video.xlsx')

        # reply
        column = 'id,video_id,video_title,data'
        self.db.cursor.execute('SELECT {} FROM reply'.format(column))

        rows = self.db.cursor.fetchall()

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

            if item[1] in meta:
                r.update(meta[item[1]])

            data.append(r)

        pd.DataFrame(data).to_excel('youtube-reply.xlsx')

        return

    def batch(self):
        if self.params.video_list is True:
            self.get_video_list()

        if self.params.reply is True:
            self.get_reply()

        if self.params.live_chat is True:
            self.get_live_chat()

        if self.params.caption is True:
            self.get_caption()

        if self.params.export is True:
            self.export()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--video-list', action='store_true', default=False, help='비디오 목록 조회')
        parser.add_argument('--reply', action='store_true', default=False, help='댓글 조회')
        parser.add_argument('--live-chat', action='store_true', default=False, help='라이브 채팅 조회')
        parser.add_argument('--caption', action='store_true', default=False, help='자막 조회')

        parser.add_argument('--export', action='store_true', default=False, help='내보내기')

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--filename', default='youtube.db', help='파일명')
        parser.add_argument('--max-scroll', default=10, type=int, help='sleep time')

        return parser.parse_args()


if __name__ == '__main__':
    YoutubeCrawler().batch()
