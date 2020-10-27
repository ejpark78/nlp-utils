#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sqlite3
import json
from time import sleep
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class NaverMovieReviews(object):

    def __init__(self):
        self.params = self.init_arguments()

        self.sleep_time = 15

        self.headers = {
            'Referer': 'https://movie.naver.com',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/86.0.4240.111 Safari/537.36'

        }

        self.conn = None
        self.cursor = None

        self.url = {
            'code': 'https://movie.naver.com/movie/sdb/browsing/bmovie.nhn?open={year}&page={page}',
            'reviews': 'https://movie.naver.com/movie/bi/mi/pointWriteFormList.nhn?'
                       'code={code}&type=after&isActualPointWriteExecute=false&isMileageSubscriptionAlready=false&'
                       'isMileageSubscriptionReject=false&page={page}',
        }

        self.template = {
            'cache': 'REPLACE INTO cache (url, content) VALUES (?, ?)',
            'code': 'INSERT INTO movie_code (url, code, title) VALUES (?, ?, ?)',
            'reviews': 'INSERT INTO movie_reviews (title, code, review) VALUES (?, ?, ?)'
        }

        self.open_db()

    def open_db(self):
        self.conn = sqlite3.connect(self.params.filename)

        self.cursor = self.conn.cursor()

        self.set_pragma(self.cursor, readonly=False)

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (url TEXT NOT NULL UNIQUE PRIMARY KEY, content TEXT)
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movie_code (url TEXT, code TEXT NOT NULL UNIQUE PRIMARY KEY, title TEXT)
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movie_reviews (title TEXT, code TEXT, review TEXT)
        ''')

        self.conn.commit()

    @staticmethod
    def set_pragma(cursor, readonly=True):
        """ sqlite 의 속도 개선을 위한 설정 """
        # cursor.execute('PRAGMA threads       = 8;')

        # 700,000 = 1.05G, 2,100,000 = 3G
        cursor.execute('PRAGMA cache_size    = 2100000;')
        cursor.execute('PRAGMA count_changes = OFF;')
        cursor.execute('PRAGMA foreign_keys  = OFF;')
        cursor.execute('PRAGMA journal_mode  = OFF;')
        cursor.execute('PRAGMA legacy_file_format = 1;')
        cursor.execute('PRAGMA locking_mode  = EXCLUSIVE;')
        cursor.execute('PRAGMA page_size     = 4096;')
        cursor.execute('PRAGMA synchronous   = OFF;')
        cursor.execute('PRAGMA temp_store    = MEMORY;')

        if readonly is True:
            cursor.execute('PRAGMA query_only    = 1;')

        return

    def exists(self, url):
        self.cursor.execute('SELECT content FROM cache WHERE url=?', (url,))

        row = self.cursor.fetchone()
        if row is not None and len(row) == 1:
            return row[0]

        return None

    def get_contents(self, url):
        content = None
        if self.params.use_cache is True:
            content = self.exists(url=url)

        is_cache = True
        if content is None:
            is_cache = False
            resp = requests.get(url=url, verify=False, headers=self.headers, timeout=120)

            self.cursor.execute(self.template['cache'], (url, resp.content,))
            self.conn.commit()

            content = resp.content

        return content, is_cache

    def save_movie_code(self, url, content):
        soup = BeautifulSoup(content, 'html5lib')

        buf = set()
        for item in soup.select('ul.directory_list li a'):
            if item.get_text() == '':
                continue

            if item['href'].find('code') < 0:
                continue

            values = (
                urljoin(url, item['href']),
                re.sub(r'^.+code=(\d+).*$', r'\g<1>', item['href']),
                item.contents[-1],
            )

            buf.add(values[1])
            print(len(buf), values[1:])

            try:
                self.cursor.execute(self.template['code'], values)
            except Exception as e:
                print(e)

        self.conn.commit()

        return ','.join(list(buf))

    def get_movie_code(self):
        years = []

        years += [y for y in range(2022, 1990, -1)]
        years += [y for y in range(1980, 1939, -10)]

        prev = ''
        for y in years:
            for p in range(1, 1000):
                url = self.url['code'].format(year=y, page=p)

                content, is_cache = self.get_contents(url=url)
                code_list = self.save_movie_code(url=url, content=content)

                if is_cache is False:
                    sleep(self.sleep_time)

                if code_list != '' and prev == code_list:
                    print('중복 목록: ', code_list)
                    break

                prev = code_list

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
                self.cursor.execute(
                    self.template['reviews'],
                    (title, code, json.dumps(review, ensure_ascii=False), )
                )
            except Exception as e:
                print(e)

        self.conn.commit()

        return ','.join(list(buf))

    def get_reviews(self):
        size = 100
        _ = self.cursor.execute('SELECT code, title FROM movie_code')

        while True:
            rows = self.cursor.fetchmany(size)
            if not rows:
                break

            for item in rows:
                print(item[0])

                prev = ''
                for p in range(1, 1000):
                    url = self.url['reviews'].format(code=item[0], page=p)

                    print(item, 'https://movie.naver.com/movie/bi/mi/basic.nhn?code=' + item[0], url)

                    content, is_cache = self.get_contents(url=url)
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

        if self.params.movie_reviews is True:
            self.get_reviews()

        self.conn.close()
        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--movie-code', action='store_true', default=False, help='영화 코드 크롤링')
        parser.add_argument('--movie-reviews', action='store_true', default=False, help='리뷰 크롤링')

        parser.add_argument('--filename', default='naver_movie_reviews.db', help='파일명')

        return parser.parse_args()


if __name__ == '__main__':
    NaverMovieReviews().batch()
