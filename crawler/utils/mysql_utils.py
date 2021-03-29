#!./venv/bin/python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pymysql
import pytz
import urllib3
from dateutil.parser import parse as parse_date

from crawler.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


class MysqlUtils(object):

    def __init__(self):
        self.params = {}

        self.db: pymysql.connections.Connection = None

        self.sql = ''
        self.column_keys = []
        self.column_alias = {}

        self.logger = Logger()
        self.timezone = pytz.timezone('Asia/Seoul')

    def create_table(self, table_name: str) -> None:
        sql = f"""
        CREATE TABLE {table_name} (
            `index` VARCHAR(50) NOT NULL,
            `id` VARCHAR(50) NOT NULL,
            `paragraph_id` INTEGER NOT NULL,
            `sentence_id` INTEGER NOT NULL,
            `date` DATETIME NOT NULL,
            `position` VARCHAR(10) NOT NULL,
            `source` VARCHAR(10) DEFAULT '',
            `category` VARCHAR(50) DEFAULT '',
            `page` VARCHAR(10) DEFAULT '',
            `text` TEXT NOT NULL,
            `ne` TEXT NOT NULL,
            `pos` TEXT NOT NULL,
            PRIMARY KEY (`index`, `id`, `paragraph_id`, `sentence_id`)
        )      
        """

        cursor = self.db.cursor()
        cursor.execute(sql)
        return

    def make_sql_frame(self, table_name: str) -> None:
        self.column_alias = {
            '_index': 'index',
            '_id': 'id',
            'paragraph_id': 'paragraph_id',
            'sentence_id': 'sentence_id',
            'position': 'position',
            'source': 'source',
            'category': 'category',
            'date': 'date',
            'text': 'text',
            'paper': 'page',
            'ne_str': 'ne',
            'morp_str': 'pos',
        }

        self.column_keys = list(set(self.column_alias.keys()))

        str_col = '`' + '`,`'.join([self.column_alias[x] for x in self.column_keys]) + '`'
        str_val = ','.join(['%s'] * len(self.column_keys))

        self.sql = f'REPLACE INTO `{table_name}` ({str_col}) VALUES ({str_val})'

        return

    def get_values(self, doc: dict) -> list:
        result = []
        for col in self.column_keys:
            if col not in doc:
                result.append('')
                continue

            result.append(doc[col])

        return result

    def save_result(self, doc_list: list) -> None:
        if len(doc_list) == 0:
            return

        cursor = self.db.cursor()

        for doc in doc_list:
            if 'date' in doc:
                doc['date'] = parse_date(doc['date']).astimezone(tz=self.timezone)

            try:
                cursor.execute(self.sql, self.get_values(doc=doc))
            except Exception as e:
                self.logger.error(msg={'level': 'ERROR', 'doc': doc, 'error': str(e)})

        self.db.commit()

        return

    def get_ids(self, date_range: str) -> list:
        # SELECT `index`, `id` FROM `naver` GROUP BY `index`, `id`;
        dt_st, dt_en = date_range.split('~')

        sql = f"""
        SELECT `index`, `id`, ANY_VALUE(`date`) 
        FROM `naver` 
        WHERE `date` 
        BETWEEN {dt_st} AND {dt_en} 
        GROUP BY `index`, `id`
        """

        cursor = self.db.cursor()
        cursor.execute(sql)

        columns = 'index,id,date'.split(',')

        return [dict(zip(columns, val)) for val in cursor.fetchall()]

    def open(self, host: str, auth: str, database: str, table_name: str) -> None:
        self.make_sql_frame(table_name=table_name)

        db_user, db_passwd = auth.split(':')
        self.db = pymysql.connect(host=host, user=db_user, password=db_passwd, database=database)

        return

    def close(self) -> None:
        if self.db:
            self.db.close()

        return


if __name__ == '__main__':
    pass
