#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import sqlite3
from os import makedirs
from os.path import dirname, isdir

import pandas as pd
import urllib3
from tqdm import tqdm

from utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CacheBase(object):

    def __init__(self, filename):
        super().__init__()

        self.logger = Logger()

        self.conn = None
        self.cursor = None

        self.schema = []

        self.open_db(filename)

    def __del__(self):
        if self.cursor is not None:
            self.cursor = None

        if self.conn is not None:
            self.conn.commit()
            self.conn.close()

            self.conn = None

        pass

    def open_db(self, filename):
        if filename is None:
            return

        path = dirname(filename)
        if isdir(path) is False:
            makedirs(path)

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

    @staticmethod
    def save_excel(filename, df, size=500000):
        writer = pd.ExcelWriter(filename + '.xlsx', engine='xlsxwriter')

        if len(df) > size:
            for pos in range(0, len(df), size):
                end_pos = pos + size if len(df) > (pos + size) else len(df)

                df[pos:pos + size].to_excel(
                    writer,
                    index=False,
                    sheet_name='{:,}-{:,}'.format(pos, end_pos)
                )
        else:
            df.to_excel(writer, index=False, sheet_name='sheet')

        writer.save()

        return

    def save(self, filename, rows):
        df = pd.DataFrame(rows)

        df.to_json(
            '{filename}.json.bz2'.format(filename=filename),
            force_ascii=False,
            compression='bz2',
            orient='records',
            lines=True,
        )

        self.save_excel(filename=filename, df=df)
        return

    def json2xlsx(self, filename):
        df = pd.read_json(
            '{filename}.json.bz2'.format(filename=filename),
            compression='bz2',
            orient='records',
            lines=True,
        )

        self.save_excel(filename=filename, df=df)
        return

    def export_tbl(self, filename, tbl, column, json_column, columns=None, stop_columns=None, xlsx=True, size=20000):
        if columns is None:
            columns = []

        if stop_columns is None:
            stop_columns = []

        fp = bz2.open(filename, 'wb')

        self.cursor.execute('SELECT {column} FROM {tbl}'.format(column=column, tbl=tbl))

        rows = self.cursor.fetchmany(size)
        while rows:
            for values in tqdm(rows):
                doc = dict(zip(column.split(','), values))

                if json_column is not None:
                    content = json.loads(doc[json_column])
                    del doc[json_column]

                    for c in stop_columns:
                        if c not in content:
                            continue

                        del content[c]

                    doc.update(content)

                new_doc = {}
                if len(columns) > 0:
                    for c in columns:
                        if c not in doc:
                            continue

                        new_doc[c] = doc[c]
                else:
                    new_doc = doc

                line = json.dumps(new_doc, ensure_ascii=False) + '\n'
                fp.write(line.encode('utf-8'))

            fp.flush()

            rows = self.cursor.fetchmany(size)

        fp.close()

        if xlsx is True:
            self.json2xlsx(filename=filename.replace('.json.bz2', ''))

        return
