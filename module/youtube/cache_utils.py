#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import sqlite3
from os.path import isfile

import pytz
import urllib3

from module.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CacheUtils(object):

    def __init__(self, filename):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.use_cache = True

        self.conn = None
        self.cursor = None

        self.schema = [
            '''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT NOT NULL UNIQUE PRIMARY KEY, 
                title TEXT NOT NULL,
                reply_count NUMBER DEFAULT -1,
                tags TEXT NOT NULL,
                data TEXT NOT NULL
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS reply (
                id TEXT NOT NULL UNIQUE PRIMARY KEY, 
                video_id TEXT NOT NULL, 
                video_title TEXT NOT NULL, 
                data TEXT NOT NULL
            )
            '''
        ]

        self.template = {
            'videos': 'REPLACE INTO videos (id, title, data, tags) VALUES (?, ?, ?, ?)',
            'reply': 'REPLACE INTO reply (id, video_id, video_title, data) VALUES (?, ?, ?, ?)',
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

    def save_videos(self, v_id, title, data, tags):
        self.cursor.execute(
            self.template['videos'],
            (v_id, title, json.dumps(data, ensure_ascii=False), json.dumps(tags, ensure_ascii=False), )
        )
        self.conn.commit()
        return

    def update_reply_count(self, v_id, count):
        self.cursor.execute('UPDATE videos SET reply_count=? WHERE id=?', (count, v_id), )
        self.conn.commit()
        return

    def save_reply(self, c_id, video_id, video_title, data):
        self.cursor.execute(
            self.template['reply'],
            (c_id, video_id, video_title, json.dumps(data, ensure_ascii=False),)
        )
        self.conn.commit()
        return
