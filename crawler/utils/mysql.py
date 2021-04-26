#!./venv/bin/python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime

import pymysql
import pytz
import urllib3
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

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

    def save_result(self, doc_list: list, verbose: int = 0) -> None:
        if len(doc_list) == 0:
            return

        cursor = self.db.cursor()

        for i, doc in enumerate(doc_list):
            if 'date' in doc:
                doc['date'] = parse_date(doc['date']).astimezone(tz=self.timezone)

            v = self.get_values(doc=doc)
            if verbose == 1:
                self.logger.log(msg={**doc, 'values': v})

            try:
                cursor.execute(self.sql, v)
            except Exception as e:
                self.logger.error(msg={'level': 'ERROR', 'doc': doc, 'error': str(e)})

            if i % 10 == 9:
                self.db.commit()

        self.db.commit()

        return

    def get_date_range(self, date_range: str) -> (str, str):
        dt_st = dt_en = datetime.now(self.timezone)

        if date_range != 'today':
            dt_st, dt_en = date_range.split('~')
            dt_st, dt_en = parse_date(dt_st), parse_date(dt_en) + relativedelta(days=1)

        return dt_st.strftime('%Y-%m-%d 00:00:00'), dt_en.strftime('%Y-%m-%d 00:00:00')

    def get_ids(self, date_range: str, table_name: str) -> set:
        dt_st, dt_en = self.get_date_range(date_range=date_range)

        cursor = self.db.cursor()
        cursor.execute(
            f"SELECT `index`, `id` "
            f"  FROM `{table_name}` "
            f"  WHERE `date` BETWEEN '{dt_st}' AND '{dt_en}' "
        )

        return set([x for x in cursor.fetchall()])

    def update_idx(self, index_table: str, source_table: str, date_range: str) -> None:
        dt_st, dt_en = self.get_date_range(date_range=date_range)

        cursor = self.db.cursor()
        cursor.execute(
            f"REPLACE INTO `{index_table}` (`index`, `id`, `date`) "
            f"  SELECT `index`, `id`, ANY_VALUE(`date`) AS `date` "
            f"  FROM `{source_table}` "
            f"  WHERE `date` BETWEEN '{dt_st}' AND '{dt_en}' "
            f"  GROUP BY `index`, `id` "
        )
        return

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
