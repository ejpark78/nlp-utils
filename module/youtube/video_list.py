#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from time import sleep

from utils.logger import Logger
from utils.selenium_wire_utils import SeleniumWireUtils
from module.youtube.cache_utils import CacheUtils


class YoutubeVideoList(object):

    def __init__(self, params):
        super().__init__()

        self.params = params

        self.logger = Logger()

        self.selenium = SeleniumWireUtils(
            login=self.params.login,
            headless=self.params.headless,
            user_data_path=self.params.user_data,
        )

        self.db = CacheUtils(
            filename=self.params.filename,
            use_cache=self.params.use_cache
        )

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

        self.selenium.reset_requests()
        self.selenium.scroll(count=self.params.max_scroll, meta=meta)

        videos = []
        for x in self.selenium.get_requests(resp_url_path='/browse_ajax'):
            if hasattr(x, 'data') is False or len(x.data) < 2:
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
