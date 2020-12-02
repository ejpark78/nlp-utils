#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep

import requests
import urllib3

from module.kbsec.base import KBSecBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class KBSecReportList(KBSecBase):

    def __init__(self, params):
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
