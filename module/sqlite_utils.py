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

from module.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class SqliteUtils(object):

    def __init__(self, filename):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.use_cache = True

        self.conn = None
        self.cursor = None

        self.headers = {
            'Referer': 'https://movie.naver.com',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/86.0.4240.111 Safari/537.36'

        }

        self.template = {
            'cache': 'REPLACE INTO cache (url, content) VALUES (?, ?)',
            'code': 'INSERT INTO movie_code (url, code, title) VALUES (?, ?, ?)',
            'reviews': 'INSERT INTO movie_reviews (title, code, review) VALUES (?, ?, ?)'
        }

        self.open_db(filename)

    def __del__(self):
        pass
        # if self.cursor is not None:
        #     self.cursor = None
        #
        # if self.conn is not None:
        #     self.conn.commit()
        #     self.conn.close()
        #
        #     self.conn = None

    def open_db(self, filename):
        if filename is None or isfile(filename) is False:
            return

        self.conn = sqlite3.connect(filename)

        self.cursor = self.conn.cursor()

        self.set_pragma(self.cursor, readonly=False)

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                url TEXT NOT NULL UNIQUE PRIMARY KEY, 
                content TEXT NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movie_code (
                url TEXT NOT NULL, 
                code TEXT NOT NULL UNIQUE PRIMARY KEY, 
                title TEXT NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movie_info (
                code TEXT NOT NULL UNIQUE PRIMARY KEY, 
                info TEXT NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movie_reviews (
                title TEXT NOT NULL, 
                code TEXT NOT NULL, 
                review TEXT NOT NULL
            )
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

    def get_contents(self, url, meta):
        content = None
        if self.use_cache is True:
            content = self.exists(url=url)

        is_cache = True
        if content is None:
            is_cache = False

            resp = requests.get(url=url, verify=False, headers=self.headers, timeout=120)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'requests',
                'url': url,
                'status_code': resp.status_code,
                **meta
            })

            self.cursor.execute(self.template['cache'], (url, resp.content,))
            self.conn.commit()

            content = resp.content

        return {
            'content': content,
            'is_cache': is_cache
        }
