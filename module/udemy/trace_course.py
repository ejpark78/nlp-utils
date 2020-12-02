#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
import os
from os import rename
from os.path import getsize
from os.path import isdir, isfile, splitext
from time import sleep

import requests
import urllib3
from tqdm import tqdm

from module.udemy.base import UdemyBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class UdemyTraceCourse(UdemyBase):

    def __init__(self, params):
        super().__init__(params=params)

        self.url_info = {
            "my_courses": {
                "url": "https://ncsoft.udemy.com/api-2.0/users/me/subscribed-courses/?fields[course]=@min,visible_instructors,image_240x135,image_480x270,favorite_time,archive_time,completion_ratio,last_accessed_time,enrollment_time,is_practice_test_course,features,num_collections,published_title,buyable_object_type,remaining_time,assignment_due_date,is_assigned,next_to_watch_item,most_recent_activity&fields[user]=@min&ordering=most_recent_activity&page={page}&page_size={page_size}"
            },
            "overview": {
                "url": "https://ncsoft.udemy.com/{home}/learn/v4/overview"
            },
            "content": {
                "url": "https://ncsoft.udemy.com/{content}/learn/v4/content"
            },
            "list": {
                "url": "https://ncsoft.udemy.com/api-2.0/courses/{course_id}/cached-subscriber-curriculum-items/?{query}",
                "query": [
                    "page_size=1400",
                    "fields[lecture]=title,object_index,is_published,sort_order,created,asset,supplementary_assets,is_free",
                    "fields[quiz]=title,object_index,is_published,sort_order,type,",
                    "fields[practice]=title,object_index,is_published,sort_order,",
                    "fields[chapter]=title,object_index,is_published,sort_order,",
                    "fields[asset]=title,filename,asset_type,status,time_estimation,is_external,"
                ]
            },
            "asset": {
                "article": "https://ncsoft.udemy.com/api-2.0/assets/{asset_id}?fields[asset]=@min,status,delayed_asset_message,processing_errors,body",
                "video": "https://ncsoft.udemy.com/api-2.0/assets/{asset_id}?fields[asset]=@min,status,delayed_asset_message,processing_errors,time_estimation,stream_urls,thumbnail_url,captions,thumbnail_sprite&fields[caption]=@default,is_translation",
                "file": "https://ncsoft.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/lectures/{lecture_id}/supplementary-assets/{asset_id}/?fields[asset]=download_urls",
                "external_link": "https://ncsoft.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/lectures/{lecture_id}/supplementary-assets/{asset_id}/?fields[asset]=external_url"
            },
            "announcements": {
                "url": "https://ncsoft.udemy.com/api-2.0/courses/{course_id}/announcements/?{query}",
                "query": [
                    "courseId=1034400&is_promotional=false",
                    "fields[course_announcement]=@default,comment_thread",
                    "fields[announcement_group]=@default,user",
                    "fields[comment_thread]=@min,num_comments",
                    "fields[user]=@min,image_50x50,initials,url"
                ]
            },
            "discussions": {
                "url": "https://ncsoft.udemy.com/api-2.0/courses/{course_id}/discussions?{query}",
                "query": [
                    "fields%5Bcourse%5D=id,published_title",
                    "fields%5Bcourse_discussion%5D=@default,user,course,related_object,is_following,is_instructor,num_replies,created,num_follows",
                    "fields%5Blecture%5D=@min,title,object_index",
                    "fields%5Bpractice%5D=@min,title,object_index",
                    "fields%5Bquiz%5D=@min,title,object_index",
                    "fields%5Buser%5D=@min,image_50x50,initials,url",
                    "ordering=-is_me,-created",
                    "page=1",
                    "page_size=15"
                ]
            }
        }

    def get_course(self, course):
        """강좌 목록을 다운로드 받는다."""
        course_path = '{}/{}'.format(self.params.data_path, course['title'].replace('/', '-'))

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
            self.make_link_file(external_link=result, path=path, name=name)

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

            self.download_file(url=v['file'], filename=filename)

            sleep(self.params.sleep)
            break

        return False

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

            sleep(self.params.sleep)

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

            sleep(self.params.sleep)

        return

    @staticmethod
    def read_done_list(path):
        filename = '{}/done.txt'.format(path)
        if isfile(filename) is False:
            return set()

        with open(filename, 'r') as fp:
            return set([l.strip() for l in fp.readlines()])

    def batch(self):
        self.selenium.open(url='https://ncsoft.udemy.com/home/my-courses/learning')
        sleep(self.params.sleep)

        done_path = '{}/{}'.format(self.params.data_path, 'done')
        if isdir(done_path) is False:
            os.makedirs(done_path)

        done_list = self.read_done_list(path=self.params.data_path)
        course_list = self.open_cache(path=self.params.data_path, name='course_list')

        for course in course_list:
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
