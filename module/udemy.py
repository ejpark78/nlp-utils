#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import math
import os
from datetime import datetime
from os.path import getsize
from os.path import isdir, isfile, splitext
from time import sleep

import pytz
import requests
import urllib3
from tqdm import tqdm
from utils.selenium_wire_utils import SeleniumWireUtils

from module.web_news.config import Config
from utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class UdemyCrawler(object):
    """Udemy 강좌 다운로드 크롤러"""

    def __init__(self):
        """생성자"""
        super().__init__()

        self.params = self.init_arguments()

        self.job_id = 'business'

        self.cfg = Config(job_category='udemy', job_id=self.job_id)

        # crawler job 정보
        job_info = self.cfg.job_info

        self.url_info = job_info['url_info']

        category_name = job_info['category_name']
        self.course_list = job_info[category_name]

        self.sleep = job_info['sleep']
        self.data_path = job_info['data_path']

        self.selenium = SeleniumWireUtils(
            login=self.params.login,
            headless=self.params.headless,
            user_data_path=self.params.user_data,
        )

        self.logger = Logger()

    def get_my_course_list(self):
        """강좌 목록을 다운로드 받는다."""
        result = []
        for page in tqdm(range(1, 14), desc='course list'):
            del self.selenium.driver.requests

            url = 'https://ncsoft.udemy.com/home/my-courses/learning/?p={page}'.format(page=page)

            self.selenium.open(url=url)
            sleep(self.sleep)

            resp = self.selenium.get_requests(resp_url_path='/api-2.0/users/me/subscribed-courses/')
            if len(resp) == 0:
                break

            is_stop = False
            for r in resp:
                if 'results' not in r.data:
                    is_stop = True
                    break

                corpus_list = r.data['results']
                result += corpus_list

                self.save_cache(cache=result, path=self.data_path, name='course_list')

            if is_stop is True:
                break

        self.save_cache(cache=result, path=self.data_path, name='course_list', save_time_tag=True)

        return

    def get_course(self, course):
        """강좌 목록을 다운로드 받는다."""
        course_path = '{}/{}'.format(self.data_path, course['title'].replace('/', '-'))

        if isdir(course_path) is False:
            os.makedirs(course_path)

        self.selenium.open(
            url='https://ncsoft.udemy.com{}'.format(course['url']),
            resp_url_path='/api-2.0/courses/',
            wait_for_path='.+/api-2.0/courses/.+$',
        )

        _ = self.selenium.get_requests(resp_url_path='/api-2.0/courses/')

        # 강좌 목록 추출
        lecture_list = self.open_cache(path=course_path, name='course')
        if lecture_list is None:
            list_url = self.url_info['list']
            url = list_url['url'].format(course_id=course['id'], query='&'.join(list_url['query']))

            resp = requests.get(
                url=url,
                headers=self.selenium.headers,
                allow_redirects=True,
                verify=False,
                timeout=60
            )
            if resp.status_code == 403:
                return None

            lecture_list = resp.json()

            self.save_cache(cache=lecture_list, path=course_path, name='course')

        # 강좌 번호 초기화
        count = {
            'chapter': 1,
            'lecture': 1
        }

        for item in lecture_list['results']:
            self.logger.log(msg={
                'title': item['title']
            })

            if item['_class'] == 'chapter':
                path = '{}/{:02d}. {}'.format(course_path, count['chapter'], item['title'])
                count['chapter'] += 1

                if isdir(path) is False:
                    os.makedirs(path)
            elif item['_class'] == 'lecture':
                self.get_lecture(
                    path=course_path,
                    lecture_count=count['lecture'],
                    asset=item['asset'],
                    title=item['title'],
                    course_id=course['id'],
                    lecture_info=item,
                )

                if 'supplementary_assets' in item:
                    for supplementary_assets in item['supplementary_assets']:
                        self.get_lecture(
                            path=course_path,
                            lecture_count=count['lecture'],
                            asset=supplementary_assets,
                            title=item['title'],
                            course_id=course['id'],
                            lecture_info=item
                        )

                count['lecture'] += 1

        return course_path

    def get_lecture(self, path, lecture_count, title, asset, course_id, lecture_info):
        """강좌를 다운로드 받는다."""
        url_info = self.url_info['asset']

        name = '{:03d}. {}'.format(lecture_count, title)

        if name.find('/') >= 0:
            name = name.replace('/', ' ')

        # 속성에 따른 url 생성
        url = ''
        if asset['asset_type'] == 'Video':
            url = url_info['video'].format(asset_id=asset['id'])
        elif asset['asset_type'] == 'Article':
            url = url_info['article'].format(asset_id=asset['id'])
        elif asset['asset_type'] == 'File':
            url = url_info['file'].format(
                course_id=course_id,
                lecture_id=lecture_info['id'],
                asset_id=asset['id']
            )
        elif asset['asset_type'] == 'ExternalLink':
            url = url_info['external_link'].format(
                course_id=course_id,
                lecture_id=lecture_info['id'],
                asset_id=asset['id']
            )

        if url == '':
            return

        # 세부 강좌 목록 조회
        resp = requests.get(
            url=url,
            headers=self.selenium.headers,
            allow_redirects=True,
            verify=False,
            timeout=120
        )
        try:
            result = resp.json()
        except Exception as e:
            self.logger.error({
                'e': str(e),
            })
            return

        self.save_cache(cache=result, path=path, name=name)

        # 속성에 따른 다운로드
        if asset['asset_type'] == 'Video':
            # 비디오 저장
            if 'stream_urls' not in result:
                return

            file_exists = self.get_video(video=result['stream_urls']['Video'], path=path, name=name)
            if file_exists is False:
                # 자막 저장
                self.get_captions(captions=result['captions'], path=path, name=name)
        elif asset['asset_type'] == 'Article':
            # 노트 저장
            self.get_article(article=result, path=path, name=name)
        elif asset['asset_type'] == 'File':
            # 파일 저장
            self.get_file(file=result, path=path, name=name)
        elif asset['asset_type'] == 'ExternalLink':
            # 외부 링크
            self.get_external_link(external_link=result, path=path, name=name)

        return

    def get_video(self, video, path, name):
        """동영상을 다운로드 받는다."""
        filename = '{path}/{name}.mp4'.format(path=path, name=name)
        if isfile(filename):
            size = getsize(filename)
            if size > 1000:
                self.logger.log(msg={
                    'skip': filename
                })
                return True

        max_size = max([v['label'] for v in video if v['label'].isdecimal()])

        for v in video:
            if v['label'] != str(max_size):
                continue

            self.logger.log({
                'filename': filename,
                'max_size': max_size,
                'f': v['file'],
            })

            resp = requests.get(
                url=v['file'],
                allow_redirects=True,
                timeout=6000,
                verify=False,
                stream=True
            )

            if resp.status_code // 100 != 2:
                self.logger.error(msg={
                    'error': 'error: {}'.format(resp.text)
                })

            total_size = int(resp.headers.get('content-length', 0))
            self.logger.log(msg={
                'size': 'size: {:,}'.format(total_size)
            })

            block_size = 1024
            wrote = 0

            with open(filename + '.parted', 'wb') as fp:
                for data in tqdm(resp.iter_content(block_size),
                                 total=math.ceil(total_size // block_size), unit='KB',
                                 unit_scale=True):
                    wrote = wrote + len(data)
                    fp.write(data)

            os.rename(filename + '.parted', filename)

            sleep(self.sleep)
            break

        return False

    def get_external_link(self, external_link, path, name):
        """외부 링크를 저장한다."""
        if 'external_url' not in external_link:
            return

        filename = '{path}/{name}.desktop'.format(path=path, name=name)
        if isfile(filename):
            self.logger.log(msg={
                'get_external_link': 'skip {}'.format(filename),
            })
            return

        with open(filename, 'w') as fp:
            content = '''[Desktop Entry]
Encoding=UTF-8
Name={name}
Type=Link
URL={url}
Icon=text-html
'''.format(name=name, url=external_link['external_url'])

            fp.write(content)

        return

    def get_article(self, article, path, name):
        """아티클을 저장한다."""
        if 'body' not in article:
            return

        filename = '{path}/{name}.html'.format(path=path, name=name)
        if isfile(filename):
            self.logger.log(msg={
                'get_article': 'skip {}'.format(filename),
            })
            return

        with open(filename, 'w') as fp:
            fp.write(article['body'])

        return

    @staticmethod
    def parse_url(url):
        """url 에서 쿼리문을 반환한다."""
        from urllib.parse import urlparse, parse_qs

        url_info = urlparse(url)
        query = parse_qs(url_info.query)
        for key in query:
            query[key] = query[key][0]

        return query

    def get_file(self, file, path, name):
        """파일을 저장한다."""
        if 'download_urls' not in file:
            return

        for file_info in file['download_urls']['File']:
            url = file_info['file']

            q = self.parse_url(url=url)

            filename = '{path}/{name}'.format(path=path, name=q['filename'])
            if isfile(filename):
                self.logger.log(msg={
                    'get_file': 'skip {}'.format(filename),
                })
                continue

            resp = requests.get(
                url=url,
                allow_redirects=True,
                timeout=6000,
                verify=False,
                stream=True
            )

            if resp.status_code // 100 != 2:
                self.logger.error(msg={
                    'error': 'error: {}'.format(resp.text)
                })

            total_size = int(resp.headers.get('content-length', 0))
            self.logger.log(msg={
                'size': 'size: {:,}'.format(total_size)
            })

            block_size = 1024
            wrote = 0

            with open(filename + '.parted', 'wb') as fp:
                for data in tqdm(resp.iter_content(block_size),
                                 total=math.ceil(total_size // block_size), unit='KB',
                                 unit_scale=True):
                    wrote = wrote + len(data)
                    fp.write(data)

            os.rename(filename + '.parted', filename)

            sleep(self.sleep)

        return

    def get_captions(self, captions, path, name):
        """자막을 다운로드 받는다."""
        for cap in captions:
            resp = requests.get(
                url=cap['url'],
                allow_redirects=True,
                verify=False,
                timeout=60
            )

            _, ext = splitext(cap['title'])

            filename = '{path}/{name}.{label}{ext}'.format(path=path, name=name, ext=ext,
                                                           label=cap['video_label'])

            if isfile(filename):
                self.logger.log({
                    'get_caption': 'skip {}'.format(filename)
                })
                return

            with open(filename, 'w') as fp:
                fp.write(resp.text)

            sleep(self.sleep)

        return

    @staticmethod
    def save_cache(cache, path, name, save_time_tag=False):
        """캐쉬 파일로 저장한다."""
        data_json = json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True)

        filename = '{path}/{name}.json'.format(path=path, name=name)
        with open(filename, 'w') as fp:
            fp.write(data_json)

        if save_time_tag is True:
            dt = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y%m%d-%H%M%S')
            filename = '{path}/{name}.{dt}.json'.format(path=path, name=name, dt=dt)
            with open(filename, 'w') as fp:
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

    @staticmethod
    def read_done_list(path):
        filename = '{}/done.txt'.format(path)
        if isfile(filename) is False:
            return set()

        with open(filename, 'r') as fp:
            return set([l.strip() for l in fp.readlines()])

    def batch(self):
        """코스 목록 전체를 다운로드한다."""
        from os import rename

        if self.params.login is True:
            self.selenium.open(url='https://ncsoft.udemy.com')
            sleep(10000)

        if self.params.course_list is True:
            self.logger.log(msg={
                'MESSAGE': '코스 목록 조회'
            })

            self.get_my_course_list()

        if self.params.trace_course is True:
            self.selenium.open(url='https://ncsoft.udemy.com/home/my-courses/learning')
            sleep(self.sleep)

            done_path = '{}/{}'.format(self.data_path, 'done')
            if isdir(done_path) is False:
                os.makedirs(done_path)

            done_list = self.read_done_list(path=self.data_path)
            self.course_list = self.open_cache(path=self.data_path, name='course_list')

            for course in self.course_list:
                self.logger.log(msg={'course': course})

                title = course['title'].replace('/', '-')
                if title in done_list:
                    self.logger.log(msg={'MESSAGE': 'SKIP TITLE', 'title': title})
                    continue

                new_path = '{}/{}'.format(done_path, title)
                if isdir(new_path) is True:
                    continue

                path = self.get_course(course=course)
                if path is None:
                    continue

                rename(path, new_path)

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--login', action='store_true', default=False)
        parser.add_argument('--headless', action='store_true', default=False)

        parser.add_argument('--course-list', action='store_true', default=False)
        parser.add_argument('--trace-course', action='store_true', default=False)

        parser.add_argument('--user-data', default='./cache/selenium/udemy')

        return parser.parse_args()


if __name__ == '__main__':
    UdemyCrawler().batch()
