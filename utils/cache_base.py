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
import pytz
import urllib3
from dateutil.parser import parse as parse_date
from dotty_dict import dotty
from tqdm import tqdm

from utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CacheBase(object):

    def __init__(self, filename: str):
        super().__init__()

        self.logger = Logger()

        self.conn = None
        self.cursor = None

        self.schema = []

        self.open_db(filename=filename)

    def __del__(self):
        if self.cursor is not None:
            self.cursor = None

        if self.conn is not None:
            self.conn.commit()
            self.conn.close()

            self.conn = None

        return

    def open_db(self, filename: str) -> None:
        if filename is None:
            return

        path = dirname(filename)
        if isdir(path) is False:
            makedirs(path)

        self.conn = sqlite3.connect(filename)

        self.cursor = self.conn.cursor()

        self.set_pragma(self.cursor, readonly=False)

        if self.schema is not None:
            for item in self.schema:
                self.cursor.execute(item)

        self.conn.commit()

        return

    @staticmethod
    def set_pragma(cursor, readonly: bool = True) -> None:
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
    def save_excel(filename: str, df: pd.DataFrame, size: int = 500000) -> None:
        writer = pd.ExcelWriter(filename + '.xlsx', engine='xlsxwriter')

        if len(df) > size:
            for pos in range(0, len(df), size):
                end_pos = pos + size if len(df) > (pos + size) else len(df)
                parted = df[pos:pos + size]

                parted.to_excel(
                    writer,
                    index=False,
                    sheet_name='{:,}-{:,}'.format(pos, end_pos)
                )
        else:
            df.to_excel(writer, index=False, sheet_name='sheet')

        writer.save()

        return

    def save(self, filename: str, rows, date_columns=None) -> None:
        df = pd.DataFrame(rows)

        df.to_json(
            '{filename}.json.bz2'.format(filename=filename),
            force_ascii=False,
            compression='bz2',
            orient='records',
            lines=True,
        )

        if date_columns is not None:
            for col in date_columns:
                df[col] = df[col].apply(lambda x: pd.to_datetime(x).date())

        self.save_excel(filename=filename, df=df)
        return

    def json2xlsx(self, filename: str, date_columns: list = None) -> None:
        df = pd.read_json(
            '{filename}.json.bz2'.format(filename=filename),
            compression='bz2',
            orient='records',
            lines=True,
        )

        if date_columns is not None:
            for col in date_columns:
                df[col] = df[col].apply(lambda x: pd.to_datetime(x).date())

        self.save_excel(filename=filename, df=df)
        return

    @staticmethod
    def parse_json_column(doc: dict, columns: list = None, exclude_columns: dict = None) -> dict:
        if columns is None:
            return doc

        for col in columns:
            if col not in doc:
                continue

            content = doc[col]
            if isinstance(doc[col], str) or isinstance(doc[col], bytes):
                content = json.loads(doc[col])

            del doc[col]

            if isinstance(content, list):
                doc[col] = ' '.join(content)
                continue

            if exclude_columns is not None:
                for c in exclude_columns:
                    if c not in content:
                        continue

                    del content[c]

            doc.update(content)

        return doc

    @staticmethod
    def limit_column(doc: dict, columns: list = None) -> dict:
        if columns is None or len(columns) <= 0:
            return doc

        result = {}
        for c in columns:
            if c not in doc:
                continue

            result[c] = doc[c]

        return result

    @staticmethod
    def parse_date_column(doc: dict, columns: list = None) -> dict:
        if columns is None:
            return doc

        timezone = pytz.timezone('Asia/Seoul')
        for col in columns:
            if col not in doc:
                continue

            doc[col] = parse_date(doc[col]).astimezone(timezone).isoformat()

        return doc

    def table_size(self, tbl: str) -> int:
        self.cursor.execute('SELECT COUNT(*) FROM {tbl}'.format(tbl=tbl))

        row = self.cursor.fetchone()
        if row is None:
            return -1

        return int(row[0])

    @staticmethod
    def apply_alias(doc: dict, alias: dict = None) -> dict:
        if alias is None:
            return doc

        dot = dotty(doc)
        for col in alias.keys():
            if col == alias[col]:
                continue

            if dot.get(col) is None:
                continue

            dot[alias[col]] = dot[col]
            if isinstance(dot[col], list) is True:
                dot[alias[col]] = ' '.join(dot[col])

        return dot.to_dict()

    def export_tbl(self, filename: str, tbl: str, db_column: str = '*', size: int = 20000, alias: dict = None,
                   columns: list = None, json_columns: list = None, exclude_columns: list = None,
                   date_columns: list = None) -> None:
        p_bar = tqdm(
            desc=tbl,
            total=self.table_size(tbl=tbl),
            unit_scale=True,
            dynamic_ncols=True
        )

        if db_column is None:
            db_column = '*'

        self.cursor.execute('SELECT {column} FROM {tbl}'.format(column=db_column, tbl=tbl))
        rows = self.cursor.fetchmany(size)

        db_cols = [d[0] for d in self.cursor.description]

        fp = bz2.open(filename, 'wb')

        while rows:
            for values in rows:
                doc = dict(zip(db_cols, values))

                # parse json
                doc = self.parse_json_column(doc=doc, columns=json_columns, exclude_columns=exclude_columns)

                # apply alias
                doc = self.apply_alias(doc=doc, alias=alias)

                # limit columns
                doc = self.limit_column(doc=doc, columns=columns)

                # pars date column
                doc = self.parse_date_column(doc=doc, columns=date_columns)

                # write line
                line = json.dumps(doc, ensure_ascii=False) + '\n'
                fp.write(line.encode('utf-8'))

                p_bar.update(1)

            fp.flush()
            rows = self.cursor.fetchmany(size)

        fp.close()

        return
