#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
import re
from argparse import Namespace
from collections import defaultdict
from datetime import datetime
from os import getenv
from os.path import isfile
from time import time, sleep

import pytz
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CrawlerIndexState(object):
    """크롤링 속도 측정"""

    def __init__(self):
        super().__init__()

        self.params = None
        self.doc_count = defaultdict(dict)
        self.total = defaultdict(int)

        self.url, self.auth = None, None

        self.last_time = time()
        self.timezone = pytz.timezone('Asia/Seoul')

    def update_count(self) -> None:
        resp = requests.get(url=self.url, auth=self.auth, verify=False)

        for line in resp.text.split('\n'):
            if line.strip() == '' or line[0] == '.' or line.find('index') == 0:
                continue

            if self.params.grep and line.find(self.params.grep) < 0:
                continue

            index, count = re.sub(r'\s+', '\t', line).split('\t', maxsplit=1)
            count = int(count)

            if index not in self.doc_count:
                self.doc_count[index] = {}

            for col, default in [('count', count)]:
                if col not in self.doc_count[index]:
                    self.doc_count[index][col] = default

            diff = count - self.doc_count[index]['count']
            sleep_time = time() - self.last_time

            self.doc_count[index].update({
                'count': count,
                'diff': diff,
                'speed': abs(diff) / sleep_time if diff > 0 else 0,
            })

            for col, val in self.doc_count[index].items():
                if isinstance(val, str):
                    continue

                self.total[col] += val

        self.last_time = time()

        return

    def show(self) -> None:
        date = datetime.now(tz=self.timezone).strftime('%Y-%m-%d %H:%M:%S')

        line = '{date: <35} {count: >10,} {diff: >7,} {speed: >7.2f} (doc/sec)\n'.format(date=date, **self.total)
        print(line)

        for index, item in self.doc_count.items():
            if self.params.active and item['diff'] == 0:
                continue

            line = '{index: <35} {count: >10,} {diff: >7,} {speed: >7.2f} (doc/sec)'.format(index=index, **item)
            print(line)

        line = '\n{name: <35} {count: >10,} {diff: >7,} {speed: >7.2f} (doc/sec)\n'.format(name='total', **self.total)
        print(line)

        return

    def load_cache(self) -> None:
        if not self.params.cache or isfile(self.params.cache) is False:
            return

        with open(self.params.cache, 'r') as fp:
            cache = json.load(fp=fp)

            self.last_time = cache['time']
            self.doc_count = cache['doc_count']

        return

    def save_cache(self) -> None:
        if not self.params.cache:
            return

        with open(self.params.cache, 'w') as fp:
            json.dump({'doc_count': self.doc_count, 'time': self.last_time}, fp=fp, ensure_ascii=False, indent=4)

        return

    def batch(self) -> None:
        self.params = self.init_arguments()

        self.url = f'{self.params.host}/_cat/indices?v&s=index&h=index,docs.count'
        self.auth = tuple(self.params.auth.split(':'))

        if not self.params.cache and isfile(self.params.cache) is True:
            os.remove(self.params.cache)

        while True:
            self.load_cache()

            self.update_count()
            self.show()

            self.save_cache()

            if self.params.sleep <= 0:
                break

            sleep(self.params.sleep)

        return

    @staticmethod
    def init_arguments() -> Namespace:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--active', action='store_true', default=False, help='변경이 있는 인덱스')

        parser.add_argument('--sleep', default=0, type=float, help='sleep time')

        parser.add_argument('--host', default=getenv('ELASTIC_SEARCH_HOST', default=None), type=str,
                            help='elasticsearch 주소')
        parser.add_argument('--auth', default=getenv('ELASTIC_SEARCH_AUTH', default=None), type=str,
                            help='elastic auth')

        parser.add_argument('--cache', default=getenv('CACHE_FILE', default=None), type=str, help='캐시 파일명')

        parser.add_argument('--grep', default=None, type=str, help='인덱스 필터')

        return parser.parse_args()


if __name__ == '__main__':
    CrawlerIndexState().batch()
