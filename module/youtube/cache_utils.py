#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

import urllib3

from utils.cache_base import CacheBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CacheUtils(CacheBase):

    def __init__(self, filename, use_cache=True):
        super().__init__(filename=filename)

        self.use_cache = use_cache

        self.schema = [
            '''
            CREATE TABLE IF NOT EXISTS channels (
                id TEXT NOT NULL UNIQUE PRIMARY KEY, 
                date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                title TEXT NOT NULL,
                video_count INTEGER DEFAULT -1,
                data TEXT NOT NULL
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT NOT NULL UNIQUE PRIMARY KEY, 
                date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                title TEXT NOT NULL,
                reply_count INTEGER DEFAULT -1,
                total INTEGER DEFAULT -1,
                tags TEXT NOT NULL,
                data TEXT NOT NULL
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS reply (
                no INTEGER PRIMARY KEY AUTOINCREMENT, 
                date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                id TEXT NOT NULL UNIQUE, 
                video_id TEXT NOT NULL, 
                video_title TEXT NOT NULL, 
                data TEXT NOT NULL
            )
            '''
        ]

        self.template = {
            'channels': 'REPLACE INTO channels (id, title, data) VALUES (?, ?, ?)',
            'video_count': 'UPDATE channels SET video_count=? WHERE id=?',
            'videos': 'REPLACE INTO videos (id, title, data, tags) VALUES (?, ?, ?, ?)',
            'reply': 'REPLACE INTO reply (id, video_id, video_title, data) VALUES (?, ?, ?, ?)',
            'reply_count': 'UPDATE videos SET reply_count=? WHERE id=?',
            'total': 'UPDATE videos SET total=? WHERE id=?',
        }

        self.open_db(filename)

    def get_video_count(self, c_id):
        self.cursor.execute('SELECT video_count FROM channels WHERE id=?', (c_id,))

        row = self.cursor.fetchone()
        if row is not None and len(row) == 1:
            return row[0]

        return -1

    def save_channels(self, c_id, title, data):
        self.cursor.execute(
            self.template['channels'],
            (c_id, title, json.dumps(data, ensure_ascii=False),)
        )
        self.conn.commit()
        return

    def save_videos(self, v_id, title, data, tags):
        self.cursor.execute(
            self.template['videos'],
            (v_id, title, json.dumps(data, ensure_ascii=False), json.dumps(tags, ensure_ascii=False),)
        )
        self.conn.commit()
        return

    def update_video_count(self, c_id, count):
        self.cursor.execute(self.template['video_count'], (count, c_id), )
        self.conn.commit()
        return

    def update_reply_count(self, v_id, count):
        self.cursor.execute(self.template['reply_count'], (count, v_id), )
        self.conn.commit()
        return

    def update_total(self, v_id, total):
        self.cursor.execute(self.template['total'], (total, v_id), )
        self.conn.commit()
        return

    def save_reply(self, c_id, video_id, video_title, data):
        self.cursor.execute(
            self.template['reply'],
            (c_id, video_id, video_title, json.dumps(data, ensure_ascii=False),)
        )
        self.conn.commit()
        return
