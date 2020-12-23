#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import re
from os.path import isfile

from tqdm import tqdm

from utils.cache_base import CacheBase


class CacheUtils(CacheBase):

    def __init__(self, filename: str = None):
        super().__init__(filename=filename)

        self.schema = None
        self.template = None

        self.filename = filename

        self.open_db(filename=self.filename)

    @staticmethod
    def change_case(text: str) -> str:
        return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', text)).lower()

    def get_properties(self, mappings: dict) -> dict:
        props = mappings['properties']
        return {self.change_case(col): props[col]['type'] if 'type' in props[col] else 'json' for col in props}

    def create_db(self, properties: dict, tbl: str, filename: str = None) -> list:
        if filename is not None:
            self.filename = filename

        properties.update({
            '_id': 'TEXT NOT NULL UNIQUE PRIMARY KEY',
            '_index': 'TEXT',
        })

        cols = set()
        columns = set()
        for col in properties.keys():
            cols.add(col)

            columns.add('`{column}` {type}'.format(
                column=col,
                type=properties[col].upper() if properties[col] != 'json' else 'text'
            ))

        cols = list(cols)
        columns = list(columns)

        self.schema = [
            'CREATE TABLE IF NOT EXISTS `{tbl}` ({columns})'.format(tbl=tbl, columns=','.join(columns))
        ]

        self.template = {
            tbl: 'REPLACE INTO `{tbl}` ({columns}) VALUES ({values})'.format(
                tbl=tbl,
                values=','.join(['?'] * len(cols)),
                columns="`{}`".format("`,`".join(cols)),
            ),
        }

        self.open_db(filename=self.filename)

        return cols

    @staticmethod
    def get_values(document: dict, column_list: list) -> list:
        result = []
        for col in column_list:
            if col not in document.keys():
                document[col] = ''

            if isinstance(document[col], dict) or isinstance(document[col], list):
                document[col] = json.dumps(document[col], ensure_ascii=False)

            result.append(document[col])

        return result

    def json2db(self, filename: str, tbl: str = 'documents') -> None:
        if isfile(filename) is not True:
            return

        with bz2.open(filename, 'rt') as fp:
            p_bar = tqdm(fp, desc=filename)
            count = 0
            columns = None

            for line in p_bar:
                doc = json.loads(line)

                if columns is None and 'mappings' in doc:
                    columns = self.create_db(
                        tbl=tbl,
                        filename=filename.replace('.json.bz2', '.db'),
                        properties=self.get_properties(mappings=doc['mappings']),
                    )
                    continue

                doc = self.apply_alias(
                    doc=doc,
                    alias={self.change_case(x): x for x in doc.keys()}
                )

                values = self.get_values(document=doc, column_list=columns)
                self.cursor.execute(self.template[tbl], values)

                count += 1
                if count % 5000 == 0:
                    p_bar.set_description(desc='{}: {:,}'.format(filename, count))
                    self.conn.commit()

            self.conn.commit()

        return
