#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from time import sleep
from urllib.parse import urljoin
import requests

import pytz
import urllib3
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.rrule import rrule, WEEKLY, MO
from urllib.parse import urlparse, parse_qs

from module.sqlite_utils import SqliteUtils
from module.utils.logger import Logger
from module.utils.selenium_wire_utils import SeleniumWireUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DaumMovieReviews(object):

    def __init__(self):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.params = self.init_arguments()

        self.sleep_time = 15

        self.url = {
            'code': 'https://movie.daum.net/boxoffice/weekly?startDate={year}{month:02d}{day:02d}',
            'info': 'https://movie.daum.net/moviedb/main?movieId={code}',
            'grade': 'https://movie.daum.net/moviedb/grade?movieId={code}',
            'post': 'https://comment.daum.net/apis/v1/ui/single/main/@{code}',
            'reviews': 'https://comment.daum.net/apis/v1/posts/{post_id}/comments?'
                       'parentId=0&offset={offset}&limit=10&sort=RECOMMEND&isInitial=false&hasNext=true',
        }

        self.db = SqliteUtils(filename=self.params.filename)
        self.db.use_cache = self.params.use_cache

    def save_movie_code(self, url, content):
        soup = BeautifulSoup(content, 'html5lib')

        buf = set()
        for item in soup.select('ul.list_movie li div.info_tit a'):
            if item.get_text() == '':
                continue

            if item['href'].find('movieId') < 0:
                continue

            values = (
                urljoin(url, item['href']),
                re.sub(r'^.+movieId=(\d+).*$', r'\g<1>', item['href']),
                item.contents[-1],
            )

            buf.add(values[1])
            print(len(buf), values[1:])

            try:
                self.db.cursor.execute(self.db.template['code'], values)
            except Exception as e:
                print(e)

        self.db.conn.commit()

        return ','.join(list(buf))

    def get_movie_code(self):
        timezone = pytz.timezone('Asia/Seoul')

        dt_list = sorted(list(
            rrule(
                freq=WEEKLY,
                byweekday=MO,
                dtstart=parse_date('2004-01-01').astimezone(self.timezone),
                until=parse_date('2020-10-27').astimezone(timezone)
            )), reverse=True)

        for dt in dt_list:
            url = self.url['code'].format(year=dt.year, month=dt.month, day=dt.day)

            contents = self.db.get_contents(url=url, meta={})
            _ = self.save_movie_code(url=url, content=contents['content'])

            if contents['is_cache'] is False:
                sleep(self.sleep_time)

        return

    def save_movie_reviews(self, code, title, content, meta):
        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '영화 리뷰 저장',
            **meta
        })

        reviews = json.loads(content)

        for item in reviews:
            try:
                self.db.cursor.execute(
                    self.db.template['reviews'],
                    (title, code, json.dumps(item, ensure_ascii=False),)
                )
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '영화 리뷰 저장 오류',
                    'error': str(e),
                    'content': content,
                    **meta
                })

        self.db.conn.commit()

        return

    @staticmethod
    def parse_comments_info(url, post, comment_info):
        post_id = post.data['post']['id']

        q = parse_qs(urlparse(url).query)
        query = dict(zip(q.keys(), [x[0] for x in q.values()]))

        size = int(query['limit'])
        total = comment_info.data['count'] + size

        return {
            'size': size,
            'total': total,
            'post_id': post_id,
        }

    def get_movie_reviews(self):
        selenium = SeleniumWireUtils()

        _ = self.db.cursor.execute('SELECT code, title FROM movie_code')

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '영화 정보',
                'code': item[0],
                'title': item[1],
                'position': i,
                'size': len(rows)
            })

            info_url = self.url['info'].format(code=item[0])
            resp = selenium.open(url=info_url, wait_for_path=r'/apis/v1/comments/on/\d+/flag')

            info = {
                'post': resp[0],
                'comments': resp[1],
                'comments_info': resp[2],
            }

            self.db.save_cache(url=info['post'].url, content=info['post'].response.body)
            self.db.save_cache(url=info['comments'].url, content=info['comments'].response.body)

            self.save_movie_reviews(
                title=item[1],
                code=item[0],
                content=info['comments'].response.body,
                meta={
                    'title': item[1],
                    'url': info['comments'].url,
                    'position': i,
                    'size': len(rows)
                }
            )

            comments_info = self.parse_comments_info(
                url=info['comments'].url,
                post=info['post'],
                comment_info=info['comments_info']
            )

            for offset in range(comments_info['size'], comments_info['total'], comments_info['size']):
                reviews_url = self.url['reviews'].format(post_id=comments_info['post_id'], offset=offset)

                if offset // 2000 > 0 and offset % 2000 == 0:
                    _ = selenium.open(url=info_url, wait_for_path=r'/apis/v1/comments/on/\d+/flag')

                contents = self.db.get_contents(
                    url=reviews_url,
                    meta={
                        'title': item[1],
                        'url': info['comments'].url,
                        'position': i,
                        'size': len(rows)
                    },
                    headers=selenium.headers
                )

                self.save_movie_reviews(
                    title=item[1],
                    code=item[0],
                    content=contents['content'],
                    meta={
                        'title': item[1],
                        'url': reviews_url,
                        'position': i,
                        'offset': offset,
                        'size': len(rows)
                    }
                )

                if contents['is_cache'] is False:
                    sleep(self.sleep_time)

        return

    def batch(self):
        if self.params.movie_code is True:
            self.get_movie_code()

        if self.params.movie_reviews is True:
            self.get_movie_reviews()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--movie-code', action='store_true', default=False, help='영화 코드 크롤링')
        parser.add_argument('--movie-info', action='store_true', default=False, help='영화 정보 크롤링')
        parser.add_argument('--movie-reviews', action='store_true', default=False, help='리뷰 크롤링')

        parser.add_argument('--filename', default='daum_movie_reviews.db', help='파일명')

        return parser.parse_args()


if __name__ == '__main__':
    DaumMovieReviews().batch()
