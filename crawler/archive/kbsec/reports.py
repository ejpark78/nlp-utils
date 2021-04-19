#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os.path import dirname
from time import sleep

import urllib3
from bs4 import BeautifulSoup

from crawler.kbsec.base import KBSecBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class KBSecReports(KBSecBase):

    def __init__(self, params):
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

        _ = self.db.cursor.execute('SELECT documentid FROM report_list WHERE state != ?', ('done',))

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

            self.download_file(
                url='http://rdata.kbsec.com/pdf_data/{}.pdf'.format(doc_id),
                filename='{}/pdf/{}.pdf'.format(dirname(self.params.cache), doc_id)
            )

            sleep(self.params.sleep)

        return
