#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sqlite3
from os.path import isfile

import pytz
import requests
import urllib3
from requests_html import HTMLSession

from module.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CacheUtils(object):

    def __init__(self, filename):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.session = HTMLSession()

        self.use_cache = True

        self.conn = None
        self.cursor = None

        self.headers = {
            'Referer': 'https://movie.naver.com',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/86.0.4240.111 Safari/537.36'

        }

        self.schema = [
            '''
                CREATE TABLE IF NOT EXISTS cache (
                    url TEXT NOT NULL UNIQUE PRIMARY KEY, 
                    content TEXT NOT NULL
                )
            ''',
            '''
                CREATE TABLE IF NOT EXISTS movie_code (
                    url TEXT NOT NULL, 
                    code TEXT NOT NULL UNIQUE PRIMARY KEY, 
                    title TEXT NOT NULL,
                    review_count INTEGER DEFAULT -1,
                    total INTEGER DEFAULT -1
                )
            ''',
            '''
                CREATE TABLE IF NOT EXISTS movie_reviews (
                    no INTEGER PRIMARY KEY AUTOINCREMENT, 
                    title TEXT NOT NULL, 
                    code TEXT NOT NULL, 
                    review TEXT NOT NULL
                )
            '''
        ]

        self.template = {
            'cache': 'REPLACE INTO cache (url, content) VALUES (?, ?)',
            'code': 'INSERT INTO movie_code (url, code, title) VALUES (?, ?, ?)',
            'reviews': 'INSERT INTO movie_reviews (title, code, review) VALUES (?, ?, ?)',
            'review_count': 'UPDATE movie_code SET review_count=? WHERE code=?',
            'total': 'UPDATE movie_code SET total=? WHERE code=?',
        }

        self.open_db(filename)

    def __del__(self):
        # if self.cursor is not None:
        #     self.cursor = None
        #
        # if self.conn is not None:
        #     self.conn.commit()
        #     self.conn.close()
        #
        #     self.conn = None
        pass

    def open_db(self, filename):
        if filename is None:
            return

        self.conn = sqlite3.connect(filename)

        self.cursor = self.conn.cursor()

        self.set_pragma(self.cursor, readonly=False)

        for item in self.schema:
            self.cursor.execute(item)

        self.conn.commit()

        return

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

    def read_cache(self, url, meta, headers=None, use_cache=True):
        content = None
        if self.use_cache is True and use_cache is True:
            content = self.exists(url=url)

        if content is not None:
            return {
                'content': content,
                'is_cache': True
            }

        if headers is None:
            headers = self.headers

        resp = requests.get(url=url, verify=False, headers=headers, timeout=120)

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': 'requests',
            'url': url,
            'status_code': resp.status_code,
            **meta
        })

        self.save_cache(url=url, content=resp.content)

        return {
            'content': resp.content,
            'is_cache': False
        }

    def update_review_count(self, code, count):
        self.cursor.execute(self.template['review_count'], (count, code), )
        self.conn.commit()
        return

    def update_total(self, code, total):
        self.cursor.execute(self.template['total'], (total, code), )
        self.conn.commit()
        return

    def save_cache(self, url, content):
        self.cursor.execute(self.template['cache'], (url, content,))
        self.conn.commit()
        return
