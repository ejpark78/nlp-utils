#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sqlite3
import logging

from time import time


class UrlIndexDB(object):
    """
    크롤링 완료된 URL 목록을 저장하고 비교하는 클래스
    """
    def __init__(self):
        super().__init__()

        self.filename = None

        self.conn = None
        self.cursor = None

    @staticmethod
    def set_pragma(cursor, readonly=True):
        """
        sqlite 의 속도 개선을 위한 설정

        :param cursor:
        :param readonly:
        :return:
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
        """
        url 을 저장하는 캐쉬 디비(sqlite) 오픈
        :param filename:
        :param delete:
        :return:
        """
        if filename is not None:
            self.filename = filename

        if self.filename is None:
            return

        if os.path.exists(self.filename) and delete is True:
            os.remove(self.filename)

        self.conn = sqlite3.connect(self.filename)

        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS url_list (url TEXT PRIMARY KEY NOT NULL)')

        self.set_pragma(self.cursor, readonly=False)

        return

    @staticmethod
    def get_url(url):
        """
        url 문자열을 찾아서 반환

        :param url:
        :return:
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

        :param url:
        :return:
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

        :param url:
        :return:
        """
        if self.cursor is None:
            return

        url = self.get_url(url)

        sql = 'INSERT INTO url_list (url) VALUES (?)'
        try:
            self.cursor.execute(sql, (url, ))
        except sqlite3.IntegrityError:
            pass
        except Exception as e:
            logging.error('', exc_info=e)
            print('ERROR at save_url: ', url, e, flush=True)

        return

    def update_url_list(self, mongodb_info):
        """
        캐쉬 디비에 있는 url 목록을 버클리 디비에 저장

        :param mongodb_info:
        :return:
        """
        if self.cursor is None:
            return

        start_time = time()

        from utils import Utils as CrawlerUtils

        if 'collection' not in mongodb_info or mongodb_info['collection'] is None:
            print('WARN at update_url_list: no collection in db info', flush=True)
            return

        # 숫자일 경우 문자로 변경
        if isinstance(mongodb_info['collection'], int) is True:
            mongodb_info['collection'] = str(mongodb_info['collection'])

        if 'port' not in mongodb_info:
            mongodb_info['port'] = 27017

        # 디비 연결
        connect, mongodb = CrawlerUtils().open_db(
            host=mongodb_info['host'], db_name=mongodb_info['name'], port=mongodb_info['port'])

        collection = mongodb.get_collection(mongodb_info['collection'])
        cursor = collection.find({}, {'url': 1, '_id': 0})[:]

        count = 0
        for document in cursor:
            if 'url' in document:
                self.save_url(document['url'])

            count += 1

            if count % 2000 == 0:
                print('.', end='', flush=True)

            if count % 20000 == 0:
                print('({:,})'.format(count), end='', flush=True)
                self.conn.commit()

        cursor.close()
        connect.close()

        self.conn.commit()

        print('\ntook: {:,} {:0.4f} sec'.format(count, time() - start_time), flush=True)

        return


if __name__ == '__main__':
    pass
