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


class YoutubeVideos(object):

    def __init__(self, params):
        super().__init__()

        self.params = params

        self.logger = Logger()

        self.selenium = SeleniumWireUtils(headless=True)

        self.db = CacheUtils(filename=self.params.filename)
        self.db.use_cache = self.params.use_cache

    @staticmethod
    def read_config(filename, column):
        with open(filename, 'r') as fp:
            buf = [x.strip() for x in fp.readlines()]

            config = json.loads(''.join(buf))

            result = config[column]

        return result

    def save_videos(self, videos, tab_name, tags):
        if tab_name == 'videos':
            video_list = [x['gridVideoRenderer'] for x in videos]
        else:
            video_list = [x['gridPlaylistRenderer'] for x in videos]

        for item in video_list:
            self.db.save_videos(
                v_id=item['videoId'],
                title=item['title']['runs'][0]['text'],
                data=item,
                tags=tags,
            )

        return

    def get_videos(self, url, meta, tags, tab_name='videos'):
        self.selenium.open(url=url)

        init_data = self.selenium.driver.execute_script('return window["ytInitialData"]')
        if init_data is None:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '동영상 목록 조회 에러: empty init data',
                **meta
            })
            return -1

        tabs = init_data['contents']['twoColumnBrowseResultsRenderer']['tabs']
        tab = tabs[2]
        if tab_name == 'videos':
            tab = tabs[1]

        contents = tab['tabRenderer']['content']['sectionListRenderer']['contents']
        result = contents[0]['itemSectionRenderer']['contents'][0]['gridRenderer']['items']

        self.save_videos(videos=result, tab_name=tab_name, tags=tags)

        return self.get_more_videos(video_count=len(result), meta=meta, tab_name=tab_name, tags=tags)

    def get_more_videos(self, video_count, meta, tab_name, tags, max_try=500, max_zero_count=10):
        if max_try < 0 or max_zero_count < 0:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'videos 조회 종료',
                'max_try': max_try,
                'max_zero_count': max_zero_count,
            })
            return video_count

        del self.selenium.driver.requests
        self.selenium.scroll(count=self.params.max_scroll, meta=meta)

        videos = []
        for x in self.selenium.get_requests(resp_url_path='/browse_ajax'):
            if x.data is None or len(x.data) < 2:
                continue

            response = x.data[1]['response']
            if 'continuationContents' not in response:
                continue

            videos += response['continuationContents']['gridContinuation']['items']

        self.save_videos(videos=videos, tab_name=tab_name, tags=tags)

        video_count += len(videos)

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': 'videos 조회',
            'count': len(videos),
            'video_count': video_count,
            'max_try': max_try,
        })

        if len(videos) == 0:
            max_zero_count -= 1
        else:
            max_zero_count = 10
            sleep(self.params.sleep)

        self.get_more_videos(
            video_count=video_count,
            meta=meta,
            max_try=max_try - 1,
            max_zero_count=max_zero_count,
            tab_name=tab_name,
            tags=tags
        )

        return video_count

    def batch(self):
        template = self.read_config(filename=self.params.template, column='template')
        channel_list = self.read_config(filename=self.params.channel_list, column='channel_list')

        for i, item in enumerate(channel_list):
            c_id = ''
            url_list = []
            for col in template.keys():
                if col not in item.keys():
                    continue

                c_id = item[col]
                url_list += [x.format(**item) for x in template[col]['videos']]
                break

            video_count = self.db.get_video_count(c_id=c_id)
            if video_count > 0:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': 'SKIP CHANNEL',
                    'item': item,
                    'position': '{:,}/{:,}'.format(i, len(channel_list)),
                })
                continue

            self.db.save_channels(c_id=c_id, title=item['title'], data=item)

            video_count = 0
            for url in url_list:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '동영상 목록 조회',
                    'url': url,
                    'position': '{:,}/{:,}'.format(i, len(channel_list)),
                    **item
                })

                video_count += self.get_videos(url=url, tab_name='videos', meta=item, tags=item)
                sleep(self.params.sleep)

            self.db.update_video_count(c_id=c_id, count=video_count)

        return


class YoutubeReply(object):

    def __init__(self, params):
        super().__init__()

        self.params = params

        self.logger = Logger()

        self.selenium = SeleniumWireUtils(headless=True)

        self.db = CacheUtils(filename=self.params.filename)
        self.db.use_cache = self.params.use_cache

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
            if '천' in total_text or 'K' in total_text:
                total_text = total_text.replace('천', '').replace('K', '')

                total = float(total_text) * 1000
            elif '만' in total_text or 'M' in total_text:
                total_text = total_text.replace('만', '').replace('M', '')

                total = float(total_text) * 10000
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
        if max_try < 0 or max_zero_count < 0:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '댓글 조회 종료',
                'max_try': max_try,
                'total': total,
                'reply_sum': reply_sum,
                'max_zero_count': max_zero_count,
            })
            return reply_sum

        del self.selenium.driver.requests

        if total > 10:
            scroll_count = self.params.max_scroll if total > 20 else 3
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

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '댓글 조회',
            'count': len(replies),
            'reply_sum': reply_sum,
            'max_try': max_try,
            'total': total,
        })

        reply_sum += len(replies)

        if len(replies) == 0:
            max_zero_count -= 1
        else:
            max_zero_count = 10
            sleep(self.params.sleep)

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

    def batch(self):
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
            self.db.update_total(v_id=v_id, total=total)

            if total == 0:
                self.db.update_reply_count(v_id=v_id, count=0)
                sleep(self.params.sleep)
                continue

            reply_count = self.get_more_reply(
                v_id=v_id,
                title=title,
                meta={'title': title, 'position': i},
                total=total
            )

            self.db.update_reply_count(v_id=v_id, count=reply_count)
            sleep(self.params.sleep)

        return


class YoutubeLiveChat(object):

    def __init__(self, params):
        super().__init__()

        self.params = params

        self.logger = Logger()

        self.selenium = SeleniumWireUtils(headless=True)

        self.db = CacheUtils(filename=self.params.filename)
        self.db.use_cache = self.params.use_cache

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

        db.cursor.execute('SELECT id FROM videos WHERE data NOT LIKE ?', ('%삼프로tv%', ))

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
            YoutubeVideos(params=self.params).batch()

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
