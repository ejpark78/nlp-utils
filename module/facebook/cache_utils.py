#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

from utils.cache_base import CacheBase


class CacheUtils(CacheBase):

    def __init__(self, filename, use_cache=True):
        super().__init__(filename=filename)

        self.use_cache = use_cache

        self.schema = [
            '''
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT NOT NULL UNIQUE PRIMARY KEY,
                    date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                    reply_count INTEGER DEFAULT -1,
                    content TEXT NOT NULL
                )
            ''',
            '''
                CREATE TABLE IF NOT EXISTS replies (
                    id TEXT NOT NULL UNIQUE PRIMARY KEY,
                    post_id TEXT NOT NULL,
                    date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                    content TEXT NOT NULL
                )
            '''
        ]

        self.template = {
            'posts': 'REPLACE INTO posts (id, content) VALUES (?, ?)',
            'replies': 'REPLACE INTO replies (id, post_id, content) VALUES (?, ?, ?)',
        }

        self.open_db(filename)

    def save_post(self, document, post_id):
        self.cursor.execute(self.template['posts'], (post_id, json.dumps(document, ensure_ascii=False),))
        self.conn.commit()
        return

    def save_replies(self, document, post_id, reply_id):
        self.cursor.execute(self.template['replies'], (reply_id, post_id, json.dumps(document, ensure_ascii=False),))
        self.conn.commit()
        return
