#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sqlite3

import pytz
import urllib3

from utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CacheUtils(object):

    def __init__(self, filename, use_cache=True):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.use_cache = use_cache

        self.conn = None
        self.cursor = None

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

    def save_cache(self, url, content):
        self.cursor.execute(self.template['cache'], (url, content,))
        self.conn.commit()
        return
