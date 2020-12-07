#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os.path import splitext
from time import sleep

import pandas as pd
import urllib3

from module.kbsec.cache_utils import CacheUtils
from module.kbsec.report_list import KBSecReportList
from module.kbsec.reports import KBSecReports

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class KBSecCrawler(object):

    def __init__(self):
        """생성자"""
        super().__init__()

        self.params = self.init_arguments()

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
            df.to_excel(writer, index=False, sheet_name='review')

        writer.save()
        return

    def export_report_list(self):
        db = CacheUtils(filename=self.params.filename)

        column = 'documentid,content,state'
        db.cursor.execute('SELECT {} FROM report_list'.format(column))

        rows = db.cursor.fetchall()

        data = []
        for i, item in enumerate(rows):
            r = dict(zip(column.split(','), item))

            content = json.loads(r['content'])
            del r['content']

            r.update(content)
            data.append(r)

        df = pd.DataFrame(data)

        filename = '{}.report_list'.format(splitext(self.params.filename)[0])

        # json
        df.to_json(
            filename + '.json.bz2',
            force_ascii=False,
            compression='bz2',
            orient='records',
            lines=True,
        )

        # xlsx
        self.save_excel(filename=filename, df=df)
        return

    def export_reports(self):
        db = CacheUtils(filename=self.params.filename)

        column = 'documentid,enc,title,summary,pdf'
        db.cursor.execute('SELECT {} FROM reports WHERE pdf != ""'.format(column))

        rows = db.cursor.fetchall()

        data = []
        for i, item in enumerate(rows):
            r = dict(zip(column.split(','), item))

            pdf = json.loads(r['pdf'])
            del r['pdf']

            r.update({
                'pdf': ''.join(pdf)
            })
            data.append(r)

        df = pd.DataFrame(data)

        filename = '{}.reports'.format(splitext(self.params.filename)[0])

        # json
        df.to_json(
            filename + '.json.bz2',
            force_ascii=False,
            compression='bz2',
            orient='records',
            lines=True,
        )

        # xlsx
        self.save_excel(filename=filename, df=df)
        return

    def export(self):
        self.export_report_list()
        self.export_reports()
        return

    def batch(self):
        if self.params.report_list:
            KBSecReportList(params=self.params).batch()

        if self.params.reports:
            KBSecReports(params=self.params).batch()

        if self.params.export is True:
            self.export()

        if self.params.login:
            sleep(10000)

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--export', action='store_true', default=False, help='내보내기')

        parser.add_argument('--report-list', action='store_true', default=False)
        parser.add_argument('--reports', action='store_true', default=False)

        parser.add_argument('--login', action='store_true', default=False)
        parser.add_argument('--headless', action='store_true', default=False)
        parser.add_argument('--user-data', default='./cache/selenium/kbsec')

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--filename', default='./data/kbsec/kbsec.db', help='파일명')
        parser.add_argument('--max-scroll', default=5, type=int, help='최대 스크롤수')

        parser.add_argument('--sleep', default=5, type=float, help='sleep time')

        return parser.parse_args()


if __name__ == '__main__':
    KBSecCrawler().batch()
