#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
import sqlite3
from time import sleep
from urllib.parse import urljoin

import pytz
import requests
import urllib3
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.rrule import rrule, WEEKLY, MO

from module.sqlite_utils import SqliteUtils
from module.utils.logger import Logger

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
                       'parentId=0&offset=15&limit=5&sort=RECOMMEND&isInitial=false&hasNext=true',
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
                dtstart=parse_date('2004-01-01').astimezone(timezone),
                until=parse_date('2020-10-27').astimezone(timezone)
            )), reverse=True)

        for dt in dt_list:
            url = self.url['code'].format(year=dt.year, month=dt.month, day=dt.day)

            content, is_cache = self.db.get_contents(url=url)
            _ = self.save_movie_code(url=url, content=content)

            if is_cache is False:
                sleep(self.sleep_time)

        return

    def get_post(self):
        size = 100
        _ = self.db.cursor.execute('SELECT code, title FROM movie_code')

        while True:
            rows = self.db.cursor.fetchmany(size)
            if not rows:
                break

            for item in rows:
                print(item)

                url = self.url['info'].format(code=item[0])

                content, is_cache = self.db.get_contents(url=url)
                review_list = self.save_movie_reviews(title=item[1], code=item[0], content=content)

                if is_cache is False:
                    sleep(self.sleep_time)

        return

    def save_movie_reviews(self, code, title, content):
        soup = BeautifulSoup(content, 'html5lib')

        buf = set()
        for item in soup.select('div.score_result ul li'):
            p = item.select('div.score_reple p')[0]
            span = p.select('span')

            comment = span[-1].get_text().strip() if span is not None and len(span) > 0 else ''

            if comment == '':
                comment = p.get_text().strip()

            review = {
                'code': code,
                'title': title,
                'score': ','.join([x.get_text() for x in item.select('div.star_score em')]),
                'comment': comment,
                'is_viewer': ','.join([x.get_text() for x in p.select('span.ico_viewer')]),
                'author': item.select('div.score_reple dl dt em span')[0].get_text(),
                'date': item.select('div.score_reple dl dt em')[-1].get_text(),
                'sympathy': item.select('div.btn_area a._sympathyButton strong')[-1].get_text(),
                'not_sympathy': item.select('div.btn_area a._notSympathyButton strong')[-1].get_text(),
            }

            if review['comment'] == '':
                continue

            buf.add(review['comment'])
            buf.add(review['date'])

            print(len(buf), title, review['date'], review['comment'])

            try:
                self.db.cursor.execute(
                    self.db.template['reviews'],
                    (title, code, json.dumps(review, ensure_ascii=False),)
                )
            except Exception as e:
                print(e)

        self.db.conn.commit()

        return ','.join(list(buf))

    def get_reviews(self):
        _ = self.db.cursor.execute('SELECT code, title FROM movie_code')

        rows = self.db.cursor.fetchall()

        for item in rows:
            print(item[0])

            prev = ''
            for p in range(1, 1000):
                url = self.url['reviews'].format(code=item[0], page=p)

                print(item, 'https://movie.naver.com/movie/bi/mi/basic.nhn?code=' + item[0], url)

                content, is_cache = self.db.get_contents(url=url)
                review_list = self.save_movie_reviews(title=item[1], code=item[0], content=content)

                if is_cache is False:
                    sleep(self.sleep_time)

                if review_list == '':
                    print('리뷰 없음')
                    break

                if review_list != '' and prev == review_list:
                    print('중복 목록: ', review_list)
                    break

                prev = review_list

        return

    def batch(self):
        if self.params.movie_code is True:
            self.get_movie_code()

        if self.params.movie_post is True:
            self.get_post()

        if self.params.movie_reviews is True:
            self.get_reviews()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--movie-code', action='store_true', default=False, help='영화 코드 크롤링')
        parser.add_argument('--movie-post', action='store_true', default=False, help='포스트 코드 크롤링')
        parser.add_argument('--movie-reviews', action='store_true', default=False, help='리뷰 크롤링')

        parser.add_argument('--filename', default='daum_movie_reviews.db', help='파일명')

        return parser.parse_args()


if __name__ == '__main__':
    DaumMovieReviews().batch()
