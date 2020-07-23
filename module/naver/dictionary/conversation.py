#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import re
import sys
from datetime import datetime
from time import sleep

import requests
import urllib3
from dateutil.rrule import rrule, DAILY
from tqdm.autonotebook import tqdm

from module.dictionary_utils import DictionaryUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TodayConversationCrawler(DictionaryUtils):
    """오늘의 회화 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

    def get_conversation(self, date):
        """ """
        site = 'https://gateway.dict.naver.com/endict/kr/enko/today/{date}/conversation.dict'.format(date=date.strftime('%Y%m%d'))
        url = '{site}?callback=angular.callbacks._0'.format(site=site)

        headers = {
            'Referer': 'https://learn.dict.naver.com/conversation#/endic/{date}?tabIndex=0'.format(date=date.strftime('%Y%m%d'))
        }
        headers.update(self.headers)

        resp = requests.get(url=url, headers=headers, verify=False)

        text = re.sub(r'angular.callbacks._0\((.+)\)', r'\g<1>', resp.text)

        return json.loads(text)

    def batch(self):
        """"""
        index = 'crawler-naver-conversation'
        self.open_db(index=index)

        start_date = datetime(2017, 6, 15)
        end_date = datetime(2019, 11, 8)

        date_list = list(rrule(DAILY, dtstart=start_date, until=end_date))
        for dt in tqdm(date_list):
            print(dt)

            doc = self.get_conversation(date=dt)['data']
            if doc is None:
                continue

            doc['_id'] = doc['id']

            self.elastic.save_document(index=index, document=doc, delete=False)
            self.elastic.flush()

            start_date = dt
            sleep(5)

        return


if __name__ == '__main__':
    TodayConversationCrawler().batch()
