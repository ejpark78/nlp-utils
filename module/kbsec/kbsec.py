#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os.path import splitext
from time import sleep

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup

from module.kbsec.cache_utils import CacheUtils
from utils.logger import Logger
from utils.selenium_wire_utils import SeleniumWireUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class KBSecBase(object):

    def __init__(self, params):
        super().__init__()

        # 070890

        self.logger = Logger()

        self.params = params

        self.db = CacheUtils(filename=self.params.filename, use_cache=self.params.use_cache)

        self.selenium = SeleniumWireUtils(
            login=self.params.login,
            headless=self.params.headless,
            user_data_path=self.params.user_data,
        )

    def get_html(self, url, refresh=False, save_cache=True):
        content = None
        if refresh is False:
            content = self.db.fetch(url=url)

        is_cache = True
        if content is None:
            resp = requests.get(
                url=url,
                verify=False,
                headers=self.selenium.headers,
                timeout=120
            )

            content = resp.content
            is_cache = False

        if is_cache is False and save_cache is True:
            self.db.save_cache(url=url, content=content)

        return content, is_cache


class KBSecReportList(KBSecBase):

    def __init__(self, params):
        """생성자"""
        super().__init__(params=params)

    def get_more_report(self, page_no, meta, max_try=500, max_zero_count=10):
        if max_try < 0 or max_zero_count < 0:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '보고서 조회 종료',
                'max_try': max_try,
                'page_no': page_no,
                'max_zero_count': max_zero_count,
            })
            return

        url = 'https://rc.kbsec.com/ajax/categoryReportList.json'

        post_data = {
            'olderid': '',
            'lowTempId': '',
            'pageNo': page_no,
            'pageSize': 24,
            'registdateFrom': '20191124',
            'registdateTo': '20201124',
            'templateid': ''
        }

        resp = requests.post(
            url=url,
            json=post_data,
            verify=False,
            headers=self.selenium.headers,
            timeout=120
        )

        reports = resp.json()['response']['reportList']

        self.save_report_list(reports=reports)

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '리서치 보고서 조회',
            'count': len(reports),
            'page_no': page_no,
            'max_try': max_try,
        })

        if len(reports) == 0:
            max_zero_count -= 1
        else:
            max_zero_count = 10
            sleep(self.params.sleep)

        self.get_more_report(
            page_no=page_no + 1,
            meta=meta,
            max_try=max_try - 1,
            max_zero_count=max_zero_count,
        )

        return

    def save_report_list(self, reports):
        for rep in reports:
            self.db.save_report_list(doc_id=rep['documentid'], content=rep)
        return

    def batch(self):
        self.selenium.open(
            url='https://rc.kbsec.com/report/reportList.able',
            resp_url_path='/ajax/categoryReportList.json',
            wait_for_path='.*/ajax/categoryReportList.json.*$'
        )

        sleep(self.params.sleep)

        self.get_more_report(page_no=1, meta={})

        return


class KBSecReports(KBSecBase):

    def __init__(self, params):
        """생성자"""
        super().__init__(params=params)

    def pdf_view(self, doc_id, enc, js_body):
        body = str(BeautifulSoup(js_body)).replace('\n', ' ')
        url = body.split('surl="', maxsplit=1)[-1].split('&amp;', maxsplit=1)[0]

        url = '{}&url={}'.format(url, enc)
        resp = self.selenium.open(url=url, wait_for_path='.*/links/1$')
        sleep(self.params.sleep)

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': 'PDF 정보',
            'doc_id': doc_id,
        })

        raw = {}
        for item in resp:
            if '/texts/' not in item.url:
                continue

            if hasattr(item, 'response') is False:
                continue

            if item.response.status_code != 200:
                continue

            i = int(item.url.split('/')[-1])
            raw[i] = json.loads(item.response.body)

        raw_list = [raw[i] for i in sorted(raw.keys())]
        self.db.save_cache(url=url, content=json.dumps(raw_list))

        text_list = []
        for item in raw_list:
            for x in item:
                text_list.append(x['text'])

        self.db.save_pdf(doc_id=doc_id, pdf=json.dumps(text_list, ensure_ascii=False))

        self.db.update_state(doc_id=doc_id, state='done')

        return

    def save_detail_view(self, content):
        soup = BeautifulSoup(content, 'html5lib')

        text = '\n'.join([x.get_text('\n') for x in soup.select('div.viewCon1')])
        item = {
            'enc': soup.select('input#enc')[0]['value'],
            'title': soup.select('input#doctitle')[0]['value'],
            'doc_id': soup.select('input#topDocId')[0]['value'],
            'summary': '\n'.join([x.strip() for x in text.split('\n') if x.strip() != '']),
        }

        self.db.save_reports(**item)

        return item

    def batch(self):
        self.selenium.open(
            url='https://rc.kbsec.com/report/reportList.able',
            wait_for_path='.*/ajax/categoryReportList.json.*$'
        )
        sleep(self.params.sleep)

        _ = self.db.cursor.execute('SELECT documentid FROM report_list WHERE state!=?', ('done',))

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            doc_id = item[0]

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '상세 정보',
                'doc_id': doc_id,
                'position': '{:,}/{:,}'.format(i, len(rows)),
            })

            url = 'https://rc.kbsec.com/detailView.able?documentid={}'.format(doc_id)
            resp = self.selenium.open(
                url=url,
                wait_for_path='.*/js/researchWeb/detailView/detailView.js.*$'
            )
            sleep(self.params.sleep)

            detail = self.save_detail_view(content=self.selenium.driver.page_source)
            js_body = [x.response.body for x in resp if '/js/researchWeb/detailView/detailView.js' in x.url][0]

            self.pdf_view(enc=detail['enc'], js_body=js_body, doc_id=doc_id)
            sleep(self.params.sleep)

        return


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

        parser.add_argument('--filename', default='./data/kbsec.db', help='파일명')
        parser.add_argument('--max-scroll', default=5, type=int, help='최대 스크롤수')

        parser.add_argument('--sleep', default=5, type=float, help='sleep time')

        return parser.parse_args()


if __name__ == '__main__':
    KBSecCrawler().batch()
