#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

from tqdm import tqdm

from utils.cache_base import CacheBase


class CacheUtils(CacheBase):

    def __init__(self, filename):
        super().__init__(filename=filename)

        self.schema = [
            '''
                CREATE TABLE IF NOT EXISTS idx (
                    id TEXT NOT NULL UNIQUE PRIMARY KEY,
                    idx TEXT NOT NULL,
                    content TEXT NOT NULL
                )
            '''
        ]

        self.template = {
            'index': 'REPLACE INTO idx (id, idx, content) VALUES (?, ?, ?)',
        }

        self.open_db(filename)

    def export_index(self, es, index, columns, column_alias=None):
        count = 1
        size = 1000
        sum_count = 0
        scroll_id = ''

        p_bar = None
        while count > 0:
            resp = es.scroll(index=index, size=size, scroll_id=scroll_id, source=columns)

            count = len(resp['hits'])
            scroll_id = resp['scroll_id']

            if p_bar is None:
                p_bar = tqdm(
                    desc=index,
                    total=resp['total'],
                    unit_scale=True,
                    dynamic_ncols=True
                )

            p_bar.update(count)
            sum_count += count

            self.logger.info(msg={
                'level': 'INFO',
                'index': index,
                'count': count,
                'sum_count': sum_count,
                'total': resp['total'],
            })

            for item in resp['hits']:
                doc = self.apply_alias(doc=item['_source'], alias=column_alias)

                self.cursor.execute(
                    self.template['index'],
                    (item['_id'], item['_index'], json.dumps(doc, ensure_ascii=False),)
                )

            self.conn.commit()

        return
