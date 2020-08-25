#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import math
import os
from os.path import getsize
from os.path import isdir, isfile, splitext
from time import sleep

import requests
import urllib3
from tqdm import tqdm

from module.config import Config
from module.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class UdemyCrawler(object):
    """Udemy 강좌 다운로드 크롤러"""

    def __init__(self):
        """생성자"""
        super().__init__()

        self.job_id = 'business'

        self.cfg = Config(job_category='udemy', job_id=self.job_id)

        self.headers = None

        # crawler job 정보
        job_info = self.cfg.job_info

        self.url_info = job_info['url_info']

        self.update_token(job_info['token'])

        category_name = job_info['category_name']
        self.course_list = job_info[category_name]

        self.sleep = job_info['sleep']
        self.data_path = job_info['data_path']

        self.logger = Logger()

    def get_my_course_list(self):
        """강좌 목록을 다운로드 받는다."""
        page_size = 10

        result = []
        for page in range(1, 20):
            url = self.url_info['my_courses']['url'].format(page=page, page_size=page_size)

            resp = requests.get(
                url=url,
                headers=self.headers,
                allow_redirects=True,
                verify=False,
                timeout=60
            ).json()

            self.logger.info(msg={
                'resp': resp
            })
            if 'results' not in resp:
                break

            corpus_list = resp['results']

            result += corpus_list

            self.save_cache(cache=result, path=self.data_path, name='course_list')
            sleep(self.sleep)

        return

    def get_list(self, course):
        """강좌 목록을 다운로드 받는다."""
        path = '{}/{}'.format(self.data_path, course['title'])

        if isdir(path) is False:
            os.makedirs(path)

        # 강좌 목록 추출
        lecture_list = self.open_cache(path=path, name='course')
        if lecture_list is None:
            list_url = self.url_info['list']
            url = list_url['url'].format(course_id=course['id'], query='&'.join(list_url['query']))

            resp = requests.get(
                url=url,
                headers=self.headers,
                allow_redirects=True,
                verify=False,
                timeout=60
            )
            lecture_list = resp.json()

            self.save_cache(cache=lecture_list, path=path, name='course')

        # 강좌 번호 초기화
        count = {
            'chapter': 1,
            'lecture': 1
        }

        for item in lecture_list['results']:
            self.logger.info(msg={
                'title': item['title']
            })

            if item['_class'] == 'chapter':
                path = '{}/{}/{:02d}. {}'.format(self.data_path, course['title'], count['chapter'], item['title'])
                count['chapter'] += 1

                if isdir(path) is False:
                    os.makedirs(path)
            elif item['_class'] == 'lecture':
                self.get_lecture(
                    path=path,
                    lecture_count=count['lecture'],
                    asset=item['asset'],
                    title=item['title'],
                    course_id=course['id'],
                    lecture_info=item,
                )

                if 'supplementary_assets' in item:
                    for supplementary_assets in item['supplementary_assets']:
                        self.get_lecture(
                            path=path,
                            lecture_count=count['lecture'],
                            asset=supplementary_assets,
                            title=item['title'],
                            course_id=course['id'],
                            lecture_info=item
                        )

                count['lecture'] += 1
        return

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
            headers=self.headers,
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
                self.logger.info(msg={
                    'skip': filename
                })
                return True

        for v in video:
            if v['label'] != '720':
                continue

            self.logger.info({
                'filename': filename,
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
            self.logger.info(msg={
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
            # os.sync()

            sleep(self.sleep)
            break

        return False

    def get_external_link(self, external_link, path, name):
        """외부 링크를 저장한다."""
        if 'external_url' not in external_link:
            return

        filename = '{path}/{name}.desktop'.format(path=path, name=name)
        if isfile(filename):
            self.logger.info(msg={
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
            self.logger.info(msg={
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
                self.logger.info(msg={
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
            self.logger.info(msg={
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
            # os.sync()

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
                self.logger.info({
                    'get_caption': 'skip {}'.format(filename)
                })
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
                          'Chrome/84.0.4147.89 Safari/537.36'
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

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--course_list', action='store_true', default=False)
        parser.add_argument('--trace_course_list', action='store_true', default=False)

        return parser.parse_args()

    def batch(self):
        """코스 목록 전체를 다운로드한다."""
        args = self.init_arguments()

        if args.course_list is True:
            self.get_my_course_list()

        if args.trace_course_list is True:
            self.course_list = self.open_cache(path=self.data_path, name='course_list')

            for course in self.course_list:
                self.logger.info(msg={
                    'course': course
                })

                self.get_list(course)

        return


if __name__ == '__main__':
    UdemyCrawler().batch()
