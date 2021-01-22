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
                CREATE TABLE IF NOT EXISTS cache (
                    url TEXT NOT NULL UNIQUE PRIMARY KEY,
                    date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                    content TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT ''
                )
            ''',
            '''
                CREATE TABLE IF NOT EXISTS report_list (
                    documentid TEXT NOT NULL UNIQUE PRIMARY KEY,
                    date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                    content TEXT NOT NULL
                )
            ''',
            '''
                CREATE TABLE IF NOT EXISTS reports (
                    documentid TEXT NOT NULL UNIQUE PRIMARY KEY,
                    date TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                    enc TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    pdf TEXT DEFAULT ''
                )
            '''
        ]

        self.template = {
            'cache': 'REPLACE INTO cache (url, content) VALUES (?, ?)',
            'report_list': 'REPLACE INTO report_list (documentid, content) VALUES (?, ?)',
            'reports': 'REPLACE INTO reports (documentid, enc, title, summary) VALUES (?, ?, ?, ?)',
            'pdf': 'UPDATE reports SET pdf=? WHERE documentid=?',
            'state': 'UPDATE report_list SET state=? WHERE documentid=?',
        }

        self.open_db(filename)

    def fetch(self, url):
        self.cursor.execute('SELECT content FROM cache WHERE url=?', (url,))

        row = self.cursor.fetchone()
        if row is not None and len(row) == 1:
            return row[0]

        return None

    def save_cache(self, url, content):
        self.cursor.execute(self.template['cache'], (url, content,))
        self.conn.commit()
        return

    def save_report_list(self, doc_id, content):
        self.cursor.execute(self.template['report_list'], (doc_id, json.dumps(content, ensure_ascii=False),))
        self.conn.commit()
        return

    def save_reports(self, doc_id, enc, title, summary):
        self.cursor.execute(self.template['reports'], (doc_id, enc, title, summary,))
        self.conn.commit()
        return

    def save_pdf(self, doc_id, pdf):
        self.cursor.execute(self.template['pdf'], (pdf, doc_id,))
        self.conn.commit()
        return

    def update_state(self, doc_id, state):
        self.cursor.execute(self.template['state'], (state, doc_id,))
        self.conn.commit()
        return
