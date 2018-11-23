#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import math
import os
from os.path import isdir
from os.path import isfile
from os.path import splitext
from time import sleep

import requests
from tqdm import tqdm

from module.config import Config

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class UdemyUtils(object):
    """Udemy 강좌 다운로드 크롤러"""

    def __init__(self):
        """생성자"""
        super().__init__()

        self.job_id = 'udemy'

        self.cfg = Config(job_id=self.job_id)

        self.headers = None

        # crawler job 정보
        job_info = self.cfg.job_info

        self.url_info = job_info['url_info']

        self.update_token(job_info['token'])

        category_name = job_info['category_name']
        self.course_list = job_info[category_name]

        self.sleep = job_info['sleep']
        self.data_path = job_info['data_path']

    def batch(self):
        """코스 목록 전체를 다운로드한다."""
        for course in self.course_list:
            self.get_list(course)

        return

    def get_list(self, course):
        """강좌 목록을 다운로드 받는다."""
        path = '{}/{}'.format(self.data_path, course['name'])

        if isdir(path) is False:
            os.makedirs(path)

        # 강좌 목록 추출
        lecture_list = self.open_cache(path=path, name='course')
        if lecture_list is None:
            list_url = self.url_info['list']
            url = list_url['url'].format(course_id=course['id'], query='&'.join(list_url['query']))

            resp = requests.get(url=url, headers=self.headers, allow_redirects=True, timeout=60)
            lecture_list = resp.json()
            self.save_cache(cache=lecture_list, path=path, name='course')

        # 강좌 번호 초기화
        count = {
            'chapter': 1,
            'lecture': 1
        }

        for item in lecture_list['results']:
            logging.info('title: {}'.format(item['title']))

            if item['_class'] == 'chapter':
                path = '{}/{}/{:02d}. {}'.format(self.data_path, course['name'], count['chapter'], item['title'])
                count['chapter'] += 1

                if isdir(path) is False:
                    os.makedirs(path)
            elif item['_class'] == 'lecture':
                self.get_lecture(path=path, lecture_id=count['lecture'],
                                 asset=item['asset'], title=item['title'])
                count['lecture'] += 1
        return

    def get_lecture(self, path, lecture_id, title, asset):
        """강좌를 다운로드 받는다."""
        url_info = self.url_info['asset']

        name = '{:03d}. {}'.format(lecture_id, title)

        if name.find('/') >= 0:
            name = name.replace('/', ' ')

        # 속성에 따른 url 생성
        url = ''
        if asset['asset_type'] == 'Video':
            url = url_info['url'].format(asset_id=asset['id'],
                                         query='&'.join(url_info['query']['video']))
        elif asset['asset_type'] == 'Article':
            url = url_info['url'].format(asset_id=asset['id'],
                                         query='&'.join(url_info['query']['article']))

        if url == '':
            return

        # 세부 강좌 목록 조회
        resp = requests.get(url=url, headers=self.headers, allow_redirects=True, timeout=60)
        result = resp.json()

        self.save_cache(cache=result, path=path, name=name)

        # 속성에 따른 다운로드
        if asset['asset_type'] == 'Video':
            # 비디오 저장
            file_exists = self.get_video(video=result['stream_urls']['Video'], path=path, name=name)

            if file_exists is False:
                # 자막 저장
                self.get_captions(captions=result['captions'], path=path, name=name)
        elif asset['asset_type'] == 'Article':
            # 노트 저장
            self.get_article(article=result, path=path, name=name)

        return

    def get_video(self, video, path, name):
        """동영상을 다운로드 받는다."""
        from os.path import getsize

        filename = '{path}/{name}.mp4'.format(path=path, name=name)
        if isfile(filename):
            size = getsize(filename)
            if size > 1000:
                logging.info('skip {}'.format(filename))
                return True

        for v in video:
            if v['label'] != '720':
                continue

            logging.info(filename)
            logging.info(v['file'])

            resp = requests.get(url=v['file'], allow_redirects=True, timeout=6000, stream=True)

            if resp.status_code // 100 != 2:
                logging.error('error: {}'.format(resp.text))

            total_size = int(resp.headers.get('content-length', 0))
            logging.info('size: {:,}'.format(total_size))

            block_size = 1024
            wrote = 0

            with open(filename + '.parted', 'wb') as fp:
                for data in tqdm(resp.iter_content(block_size),
                                 total=math.ceil(total_size // block_size), unit='KB',
                                 unit_scale=True):
                    wrote = wrote + len(data)
                    fp.write(data)

            os.rename(filename + '.parted', filename)
            # os.sync()

            sleep(self.sleep)
            break

        return False

    @staticmethod
    def get_article(article, path, name):
        """아티클을 저장한다."""
        if 'body' not in article:
            return

        filename = '{path}/{name}.html'.format(path=path, name=name)
        if isfile(filename):
            logging.info('skip {}'.format(filename))
            return

        with open(filename, 'w') as fp:
            fp.write(article['body'])

        return

    def get_captions(self, captions, path, name):
        """자막을 다운로드 받는다."""
        for cap in captions:
            resp = requests.get(url=cap['url'], allow_redirects=True, timeout=60)

            _, ext = splitext(cap['title'])

            filename = '{path}/{name}.{label}{ext}'.format(path=path, name=name, ext=ext,
                                                           label=cap['video_label'])

            if isfile(filename):
                logging.info('skip {}'.format(filename))
                return

            with open(filename, 'w') as fp:
                fp.write(resp.text)

            sleep(self.sleep)

        return

    def update_token(self, token):
        """토큰 정보를 갱신한다."""
        self.headers = {
            'authorization': 'Bearer {token}'.format(token=token),
            'x-udemy-authorization': 'Bearer {token}'.format(token=token),
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/70.0.3538.77 Safari/537.36'
        }
        return

    @staticmethod
    def save_cache(cache, path, name):
        """캐쉬 파일로 저장한다."""
        filename = '{path}/{name}.json'.format(path=path, name=name)

        with open(filename, 'w') as fp:
            data_json = json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True)
            fp.write(data_json)

        return

    @staticmethod
    def open_cache(path, name):
        """캐쉬파일을 읽는다."""
        filename = '{path}/{name}.json'.format(path=path, name=name)
        if isfile(filename) is False:
            return None

        with open(filename, 'r') as fp:
            data = ''.join(fp.readlines())
            result = json.loads(data)

        return result
