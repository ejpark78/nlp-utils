#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os.path import splitext
from time import sleep

import urllib3

from module.kbsec.cache_utils import CacheUtils
from module.kbsec.report_list import KBSecReportList
from module.kbsec.reports import KBSecReports
from utils.dataset_utils import DataSetUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class KBSecCrawler(object):

    def __init__(self):
        super().__init__()

        self.params = self.init_arguments()

    def export(self):
        alias = {
            'pdf': 'text',
            'content': 'text',
            'documentid': 'report_id',
            'analystNm': 'author',
            'docTitle': 'report_title',
            'docTitleSub': 'sub_title',
            'foldertemplate': 'category',
            'docDetail': 'summary',
            'urlLink': 'pdf_link',
            'publicDate': 'date',
            'publicTime': 'time',
        }

        columns = list(set(
            'report_id,title,summary,text,pdf_link,writer,report_title,sub_title,category,date,time'.split(',')
        ))

        db = CacheUtils(filename=self.params.cache)

        f_name = '{filename}.reports'.format(filename=splitext(self.params.cache)[0])
        db.export_tbl(
            filename='{f_name}.json.bz2'.format(f_name=f_name),
            tbl='reports',
            db_column='documentid,title,summary,pdf',
            json_columns='pdf'.split(','),
            columns=columns,
            alias=alias
        )
        db.json2xlsx(filename=f_name)

        f_name = '{filename}.report_list'.format(filename=splitext(self.params.cache)[0])
        db.export_tbl(
            filename='{f_name}.json.bz2'.format(f_name=f_name),
            tbl='report_list',
            db_column='documentid,content',
            json_columns='content'.split(','),
            columns=columns,
            alias=alias
        )
        db.json2xlsx(filename=f_name)

        return

    def batch(self):
        if self.params.report_list:
            KBSecReportList(params=self.params).batch()

        if self.params.reports:
            KBSecReports(params=self.params).batch()

        if self.params.export is True:
            self.export()

        if self.params.upload is True:
            DataSetUtils().upload(filename=self.params.meta)

        if self.params.login:
            sleep(10000)

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--report-list', action='store_true', default=False)
        parser.add_argument('--reports', action='store_true', default=False)

        parser.add_argument('--export', action='store_true', default=False, help='내보내기')
        parser.add_argument('--upload', action='store_true', default=False, help='minio 업로드')

        parser.add_argument('--login', action='store_true', default=False)
        parser.add_argument('--headless', action='store_true', default=False)
        parser.add_argument('--user-data', default='./cache/selenium/kbsec')

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--cache', default='./data/kbsec/kbsec.db', help='파일명')
        parser.add_argument('--max-scroll', default=5, type=int, help='최대 스크롤수')

        parser.add_argument('--sleep', default=5, type=float, help='sleep time')

        parser.add_argument('--meta', default='./data/kbsec/meta.json', help='메타 파일명')

        return parser.parse_args()


if __name__ == '__main__':
    KBSecCrawler().batch()
