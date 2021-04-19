#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import requests
import urllib3

from crawler.utils.cache_base import CacheBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CacheUtils(CacheBase):

    def __init__(self, filename, use_cache=True):
        super().__init__(filename=filename)

        self.use_cache = use_cache

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
                    date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                    content TEXT NOT NULL
                )
            ''',
            '''
                CREATE TABLE IF NOT EXISTS movie_code (
                    url TEXT NOT NULL, 
                    date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                    code TEXT NOT NULL UNIQUE PRIMARY KEY, 
                    title TEXT NOT NULL,
                    review_count INTEGER DEFAULT -1,
                    total INTEGER DEFAULT -1
                )
            ''',
            '''
                CREATE TABLE IF NOT EXISTS movie_reviews (
                    no INTEGER PRIMARY KEY AUTOINCREMENT, 
                    date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
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
