#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from collections import defaultdict
from datetime import datetime
from os import getenv
from os.path import isfile
from time import time, sleep

import pytz
import requests
import urllib3

from crawler.utils.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CrawlerIndexState(object):
    """크롤링 속도 측정"""

    def __init__(self):
        super().__init__()

        self.params: dict = None

        self.total = defaultdict(int)
        self.doc_count = defaultdict(dict)

        self.url, self.auth = None, None

        self.last_time = time()
        self.timezone = pytz.timezone('Asia/Seoul')

    def update_count(self) -> None:
        resp = requests.get(url=self.url, auth=self.auth, verify=False)

        index_list = set()

        for line in resp.text.split('\n'):
            if line.strip() == '' or line[0] == '.':
                continue

            if self.params['grep'] and line.find(self.params['grep']) < 0:
                continue

            index, count = re.sub(r'\s+', '\t', line).split('\t', maxsplit=1)
            count = int(count)

            index_list.add(index)

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

        # delete index
        index_list = set(self.doc_count.keys()) - index_list
        for index in list(index_list):
            del self.doc_count[index]

        return

    def show(self) -> None:
        date = datetime.now(tz=self.timezone).strftime('%Y-%m-%d %H:%M:%S')

        line = '{date: <35} {count: >12,} {diff: >7,} {speed: >7.2f} (doc/sec)\n'.format(date=date, **self.total)
        print(line)

        for index, item in self.doc_count.items():
            if self.params['active'] and item['diff'] == 0:
                continue

            line = '{index: <35} {count: >12,} {diff: >7,} {speed: >7.2f} (doc/sec)'.format(index=index, **item)
            print(line)

        line = '\n{name: <35} {count: >12,} {diff: >7,} {speed: >7.2f} (doc/sec)\n'.format(name='total', **self.total)
        print(line)

        return

    def load_cache(self) -> None:
        if not self.params['cache'] or isfile(self.params['cache']) is False:
            return

        with open(self.params['cache'], 'r') as fp:
            cache = json.load(fp=fp)

            self.last_time = cache['time']
            self.doc_count = cache['doc_count']

        return

    def save_cache(self) -> None:
        if not self.params['cache']:
            return

        if self.params['sleep'] > 0:
            return

        with open(self.params['cache'], 'w') as fp:
            line = json.dumps({'doc_count': self.doc_count, 'time': self.last_time}, ensure_ascii=False, indent=4)
            fp.write(line)

        return

    def index_size(self) -> None:
        while True:
            self.load_cache()

            self.update_count()
            self.show()

            self.save_cache()

            if self.params['sleep'] <= 0:
                return

            sleep(self.params['sleep'])

        return

    def date_histogram(self, index: str, date_range: str) -> dict:
        es = ElasticSearchUtils(host=self.params['host'], http_auth=self.params['auth'])

        result = es.get_date_histogram(index=index, column='date', interval='day', date_range=date_range)

        return result

    def batch(self) -> None:
        self.params = self.init_arguments()

        self.url = f'{self.params["host"]}/_cat/indices?s=index&h=index,docs.count'
        self.auth = tuple(self.params['auth'].split(':'))

        if self.params['date_histogram']:
            self.date_histogram(index=self.params['index'], date_range=self.params['date_range'])
        else:
            self.index_size()

        return

    @staticmethod
    def init_arguments() -> dict:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--date-histogram', action='store_true', default=False, help='날짜별 문서 수량')
        parser.add_argument('--index-size', action='store_true', default=False, help='인덱스 사이즈')

        parser.add_argument('--active', action='store_true', default=False, help='변경이 있는 인덱스')

        parser.add_argument('--sleep', default=0, type=float, help='sleep time')

        parser.add_argument('--host', default=getenv('ELASTIC_SEARCH_HOST', default=None), type=str,
                            help='elasticsearch 주소')
        parser.add_argument('--auth', default=getenv('ELASTIC_SEARCH_AUTH', default=None), type=str,
                            help='elastic auth')

        parser.add_argument('--cache', default=None, type=str, help='캐시 파일명')

        parser.add_argument('--grep', default=None, type=str, help='인덱스 필터')

        parser.add_argument('--index', default=None, type=str, help='인덱스명')
        parser.add_argument('--date-range', default=None, type=str, help='날짜 범위')

        return vars(parser.parse_args())


if __name__ == '__main__':
    CrawlerIndexState().batch()
