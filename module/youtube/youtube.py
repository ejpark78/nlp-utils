#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from module.utils.elasticsearch_utils import ElasticSearchUtils
from module.utils.logger import Logger
from module.utils.selenium_wire_utils import SeleniumWireUtils
from module.youtube.cache_utils import CacheUtils
from time import sleep

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

        host = 'https://corpus.ncsoft.com:9200'
        index = 'crawler-youtube-reply'

        self.elastic = ElasticSearchUtils(
            host=host,
            index=index,
            split_index=True
        )

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

        result = tab['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['gridRenderer']['items']

        self.selenium.scroll(count=self.max_scroll, meta=meta)

        for x in self.selenium.get_requests(resp_url_path='/browse_ajax'):
            result += x.data[1]['response']['continuationContents']['gridContinuation']['items']

        if tab_name == 'videos':
            return [x['gridVideoRenderer'] for x in result]

        return [x['gridPlaylistRenderer'] for x in result]

    def get_video_list(self):
        url_list = [{
            'lang': 'en',
            'tag': 'L2',
            'title': 'Clobberstomp',
            'videos': 'https://www.youtube.com/c/Clobberstomped/videos?view=0&sort=dd&shelf_id=0',
            'playlist': 'https://www.youtube.com/c/Clobberstomped/playlists?view=1&flow=grid',
        }, {
            'lang': 'ko',
            'tag': 'economy',
            'title': '삼프로TV_경제의신과함께',
            'videos': 'https://www.youtube.com/c/%EC%82%BC%ED%94%84%EB%A1%9Ctv/videos?view=0',
            'playlist': 'https://www.youtube.com/c/%EC%82%BC%ED%94%84%EB%A1%9Ctv/playlists?view=1&flow=grid',
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

    def get_reply(self):
        _ = self.db.cursor.execute('SELECT id, title, data FROM videos WHERE reply_count < 0')

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '댓글 조회',
                'video id': item[0],
                'title': item[1],
                'position': i,
                'size': len(rows)
            })

            v_id = item[0]
            url = 'https://www.youtube.com/watch?v={v_id}'.format(v_id=v_id)
            self.selenium.open(
                url=url,
                resp_url_path=None,
                wait_for_path=None
            )

            self.selenium.scroll(count=self.max_scroll, meta={'title': item[1], 'position': i})

            replies = []
            for x in self.selenium.get_requests(resp_url_path='/comment_service_ajax'):
                resp_item = x.data['response']['continuationContents']['itemSectionContinuation']
                if 'contents' not in resp_item:
                    continue

                replies += resp_item['contents']

            replies = [x['commentThreadRenderer']['comment']['commentRenderer'] for x in replies]
            for data in replies:
                self.db.save_reply(
                    c_id=data['commentId'],
                    video_id=item[0],
                    video_title=item[1],
                    data=data
                )

            self.db.update_reply_count(v_id=v_id, count=len(replies))
            sleep(self.sleep_time)

        return

    def batch(self):
        if self.params.video_list is True:
            self.get_video_list()

        if self.params.reply is True:
            self.get_reply()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--video-list', action='store_true', default=False, help='비디오 목록 조회')
        parser.add_argument('--reply', action='store_true', default=False, help='댓글 조회')

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--filename', default='youtube.db', help='파일명')
        parser.add_argument('--max-scroll', default=30, type=int, help='sleep time')

        return parser.parse_args()


if __name__ == '__main__':
    YoutubeCrawler().batch()
