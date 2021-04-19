#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

from crawler.utils.cache_base import CacheBase


class CacheUtils(CacheBase):

    def __init__(self, filename, use_cache=True):
        super().__init__(filename=filename)

        self.use_cache = use_cache

        self.schema = [
            '''
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT NOT NULL UNIQUE PRIMARY KEY,
                    date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                    post_count INTEGER DEFAULT -1,
                    name TEXT NOT NULL,
                    content TEXT NOT NULL
                )
            ''',
            '''
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT NOT NULL UNIQUE PRIMARY KEY,
                    account_id TEXT NOT NULL,
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
            'accounts': 'REPLACE INTO accounts (id, name, content) VALUES (?, ?, ?)',
            'post_count': 'UPDATE accounts SET post_count=? WHERE id=?',
            'posts': 'REPLACE INTO posts (id, account_id, content) VALUES (?, ?, ?)',
            'reply_count': 'UPDATE posts SET reply_count=? WHERE id=?',
            'replies': 'REPLACE INTO replies (id, post_id, content) VALUES (?, ?, ?)',
        }

        self.open_db(filename)

    def save_account(self, document, name, account_id):
        self.cursor.execute(self.template['accounts'], (account_id, name, json.dumps(document, ensure_ascii=False),))
        self.conn.commit()
        return

    def save_post_count(self, account_id, count):
        self.cursor.execute(self.template['post_count'], (count, account_id), )
        self.conn.commit()
        return

    def save_post(self, document, post_id, account_id, date=None):
        if date is None:
            self.cursor.execute(self.template['posts'],
                                (post_id, account_id, json.dumps(document, ensure_ascii=False),))
        else:
            self.cursor.execute(
                'REPLACE INTO posts (id, account_id, content, date) VALUES (?, ?, ?, ?)',
                (post_id, account_id, json.dumps(document, ensure_ascii=False), date,)
            )

        self.conn.commit()
        return

    def save_reply_count(self, post_id, count):
        self.cursor.execute(self.template['reply_count'], (count, post_id), )
        self.conn.commit()
        return

    def save_replies(self, document, post_id, reply_id, date=None):
        if date is None:
            self.cursor.execute(self.template['replies'],
                                (reply_id, post_id, json.dumps(document, ensure_ascii=False),))
        else:
            self.cursor.execute(
                'REPLACE INTO replies (id, post_id, content, date) VALUES (?, ?, ?, ?)',
                (reply_id, post_id, json.dumps(document, ensure_ascii=False), date,)
            )

        self.conn.commit()
        return
