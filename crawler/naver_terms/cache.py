#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json

from crawler.utils.cache import CacheCore


class Cache(CacheCore):

    def __init__(self, filename: str, tbl: list):
        super().__init__(filename=filename)

        self.schema = [
            f'''
            CREATE TABLE IF NOT EXISTS `{tbl}` (
                `doc_id` TEXT NOT NULL UNIQUE PRIMARY KEY,
                `doc` TEXT NOT NULL,
                `crawl_date` TEXT NOT NULL DEFAULT (datetime('now','localtime')), 
                `done` INTEGER DEFAULT 0
            )
            '''
        ]

        self.open_db(filename=filename, fast=False)

    def save_doc(self, doc_id: str, doc: dict, tbl: str) -> None:
        self.cursor.execute(
            f'REPLACE INTO `{tbl}` (`doc_id`, `doc`) VALUES (?, ?)',
            (doc_id, json.dumps(doc, ensure_ascii=False),)
        )
        self.conn.commit()
        return

    def set_done(self, doc_id: str, tbl: str) -> None:
        self.cursor.execute(f'UPDATE `{tbl}` SET `done`=1 WHERE `doc_id`=?', (doc_id, ))
        self.conn.commit()
        return

    def dump(self, tbl: str, size: int) -> list:
        self.cursor.execute(f'SELECT doc FROM `{tbl}` WHERE `done` != 1')

        cols = [d[0] for d in self.cursor.description]

        return [json.loads(dict(zip(cols, x))['doc']) for x in self.cursor.fetchmany(size)]

    def dump_table(self, tbl: str, fp: bz2.BZ2File) -> None:
        self.export_tbl(
            fp=fp,
            tbl=tbl,
            db_column='doc',
            json_columns='doc'.split(','),
            date_columns=None,
            columns=None,
            alias=None
        )
        return
