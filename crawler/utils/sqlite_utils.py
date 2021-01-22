#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import os
import sqlite3

from crawler.utils.logger import Logger


class SqliteUtils(object):
    """sqlite 유틸"""

    def __init__(self, filename=None):
        """생성자"""
        self.conn = None
        self.cursor = None

        self.filename = filename

        # 디비 오픈
        self.open_db(filename=filename)

        self.logger = Logger()
        return

    def open_db(self, filename):
        """ 디비를 오픈한다. """
        if filename is None:
            return

        self.filename = filename

        # 폴더 생성
        path = os.path.dirname(filename)
        if os.path.exists(path) is not True:
            os.makedirs(path)

        # 파일 생성
        try:
            self.conn = sqlite3.connect(filename)
            self.cursor = self.conn.cursor()
        except Exception as e:
            msg = {
                'message': 'sqlite 디비 생성 오류',
                'filename': filename,
                'exception': str(e),
            }
            logging.error(msg=msg)

        return

    def close(self):
        """디비를 닫는다."""
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None

        if self.conn is not None:
            self.conn.commit()
            self.conn = None

        self.filename = None

        return

    def create_table(self, tbl_info=None):
        """테이블을 생성한다."""
        if tbl_info is None:
            tbl_info = {
                'name': 'tbl',
                'primary': 'id',
                'columns': ['raw']
            }

        columns = []
        if 'primary' in tbl_info:
            columns = [
                '{primary} TEXT PRIMARY KEY NOT NULL'.format(**tbl_info)
            ]

        for c in tbl_info['columns']:
            if 'primary' in tbl_info and c == tbl_info['primary']:
                continue

            columns.append('{} TEXT'.format(c))

        template = 'CREATE TABLE IF NOT EXISTS {name} ({columns})'
        schema = template.format(name=tbl_info['name'], columns=','.join(columns))

        try:
            # 테이블 생성
            self.cursor.execute(schema)

            self.set_pragma(self.cursor, readonly=False)

            # sql 명령 실행
            self.conn.commit()
        except Exception as e:
            log_msg = {
                'task': 'sqlite',
                'message': '테이블 생성 오류',
                'template': template,
                'schema': schema,
                'exception': e,
            }
            logging.error(msg=log_msg)

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

    def exists(self, value, column, name='tbl'):
        """ 다운 받을 문서 아이디가 인덱스 디비에 있는지 검사 """
        # url 주소 조회
        sql = 'SELECT 1 FROM {name} WHERE {column}=?'.format(name=name, column=column)
        self.cursor.execute(sql, (value,))

        row = self.cursor.fetchone()
        if row is not None and len(row) == 1:
            return True

        return False

    def save_doc(self, doc, tbl_info):
        """ 입력 받은 URL 저장 """
        schema = 'INSERT INTO {name} ({columns}) VALUES ({values})'

        values = ['?'] * len(tbl_info['columns'])
        sql = schema.format(
            name=tbl_info['name'],
            values=','.join(values),
            columns=','.join(tbl_info['columns']),
        )

        values = []
        for c in tbl_info['columns']:
            if c in doc:
                if isinstance(doc[c], dict) or isinstance(doc[c], list):
                    doc[c] = json.dumps(doc[c], ensure_ascii=False, sort_keys=True, indent=2)

                values.append(str(doc[c]))
            else:
                values.append('')

        values += []

        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            pass
        except Exception as e:
            log_msg = {
                'task': 'sqlite',
                'message': '저장 오류',
                'sql': sql,
                'values': values,
                'filename': self.filename,
                'exception': str(e),
            }
            logging.error(msg=log_msg)

        return

    def table_list(self):
        """테이블 목록을 반환한다."""
        self.cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')

        result = self.cursor.fetchone()

        self.cursor.close()

        return result

    @staticmethod
    def get_columns(cursor):
        """cursor 에서 컬럼 목록을 반환한다."""
        return [d[0] for d in cursor.description]

    def get_column_list(self, table):
        """컬럼 목록을 반환한다."""
        self.cursor.execute('SELECT * FROM {} LIMIT 1'.format(table))

        result = self.get_columns(self.cursor)

        self.cursor.close()

        return result
