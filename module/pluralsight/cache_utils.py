#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pytz
import urllib3

from utils.cache_base import CacheBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CacheUtils(CacheBase):

    def __init__(self, filename, use_cache=True):
        super().__init__(filename=filename)
        self.timezone = pytz.timezone('Asia/Seoul')

        self.use_cache = use_cache

        self.schema = [
            '''
                CREATE TABLE IF NOT EXISTS cache (
                    url TEXT NOT NULL UNIQUE PRIMARY KEY,
                    date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                    content TEXT NOT NULL
                )
            '''
        ]

        self.template = {
            'cache': 'REPLACE INTO cache (url, content) VALUES (?, ?)',
        }

        self.open_db(filename)

    def exists(self, url):
        self.cursor.execute('SELECT content FROM cache WHERE url=?', (url,))

        row = self.cursor.fetchone()
        if row is not None and len(row) == 1:
            return row[0]

        return None

    def save_cache(self, url, content):
        self.cursor.execute(self.template['cache'], (url, content,))
        self.conn.commit()
        return
