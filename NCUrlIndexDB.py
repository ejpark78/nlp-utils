#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys
import sqlite3


class NCUrlIndexDB:
    """
    크롤링 완료된 URL 목록을 저장하고 비교하는 클래스
    """
    def __init__(self):
        self.filename = None

        self.conn = None
        self.cursor = None

    @staticmethod
    def set_pragam(cursor, readonly=True):
        """
        sqlite의 속도 개선을 위한 설정
        """
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

    def open_db(self, filename=None, delete=False):
        if filename is not None:
            self.filename = filename

        if self.filename is None:
            return

        if os.path.exists(self.filename) and delete is True:
            os.remove(self.filename)

        self.conn = sqlite3.connect(self.filename)

        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS url_list (url TEXT PRIMARY KEY NOT NULL)')

        self.set_pragam(self.cursor, readonly=False)

        return

    @staticmethod
    def get_url(url):
        """
        url 문자열을 찾아서 반환
        """

        if isinstance(url, str) is True:
            return url
        elif 'simple' in url and url['simple'] != '':
            return url['simple']
        elif 'full' in url:
            return url['full']

        return url

    def check_url(self, url):
        """
        다운 받을 url 이 디비에 있는지 검사
        url 목록을 저장하는 버클리 디비에서 점검
        """
        if self.cursor is None:
            return False

        sql = 'SELECT 1 FROM url_list WHERE url=?'
        url = self.get_url(url)
        self.cursor.execute(sql, (url,))

        row = self.cursor.fetchone()
        if row is not None and len(row) == 1:
            return True

        return False

    def save_url(self, url):
        """
        입력 받은 URL 저장
        """
        if self.cursor is None:
            return

        url = self.get_url(url)

        sql = 'INSERT INTO url_list (url) VALUES (?)'
        try:
            self.cursor.execute(sql, (url, ))
        except Exception:
            print('ERROR at save_url: {} {}'.format(url, sys.exc_info()[0]), flush=True)

        self.conn.commit()
        return

    def update_url_list(self, db, collection_name):
        """
        캐쉬 디비에 있는 url 목록을 버클리 디비에 저장
        """
        if self.cursor is None:
            return

        # cursor = db[collection_name].find({}, {'url': 1, '_id': 0}, no_cursor_timeout=True)
        cursor = db[collection_name].find({}, {'url': 1, '_id': 0})[:]

        for document in cursor:
            if 'url' in document:
                self.save_url(document['url'])

        self.conn.commit()

        cursor.close()
        return

# end of NCUrlIndexDB


if __name__ == '__main__':
    pass

# end of __main__
