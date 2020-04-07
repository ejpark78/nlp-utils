#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep
from urllib.parse import unquote
from uuid import uuid4

import requests
import urllib3
from bs4 import BeautifulSoup

from module.dictionary_utils import DictionaryUtils
from module.utils.logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class YoudaoExampleSearch(DictionaryUtils):
    """사전 예문 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

    def get_status_code(self, query, url_frame):
        """ """
        url = url_frame.format(query=query)

        resp = requests.get(url)

        soup = BeautifulSoup(resp.content, 'lxml')

        status_code = soup.select_one('input#page-status')
        if status_code is None or status_code.has_attr('value') is False:
            self.logger.error(msg=LogMsg({
                'message': 'status 조회 에러',
                'url': url,
            }))
            return None

        return status_code['value']

    def trace_examples(self, url, meta):
        """ """
        import re

        resp = requests.get(url=url)

        soup = BeautifulSoup(resp.content, 'lxml')

        result = []
        for tag in soup.select('div#bilingual ul li'):
            example = [t.get_text().strip() for t in tag.select('p')]
            if len(example) == 0:
                example = ['', '']

            doc = {
                '_id': str(uuid4()),
                'source': example[2],
                'english': example[0],
                'chinese': example[1],
            }
            doc.update(meta)

            flag = re.findall(r'[\u4e00-\u9fff]+', doc['english'])
            if len(flag) != 0:
                doc['chinese'] = example[0]
                doc['english'] = example[1]

            self.elastic.save_document(document=doc, delete=False)
            result.append(doc)

        self.elastic.flush()

        return result

    @staticmethod
    def get_url_frame_info():
        """ """
        return [
            {
                'url_frame': 'http://www.youdao.com/example/{query}/',
                'meta': {
                    'category': 'all'
                },
            },
            {
                'url_frame': 'http://www.youdao.com/example/oral/{query}/',
                'meta': {
                    'category': 'oral'
                },
            },
            {
                'url_frame': 'http://www.youdao.com/example/written/{query}/',
                'meta': {
                    'category': 'written'
                },
            },
            {
                'url_frame': 'http://www.youdao.com/example/paper/{query}/',
                'meta': {
                    'category': 'paper'
                },
            },
        ]

    def trace_entry_list(self):
        """ """
        entry_list = self.read_entry_list()

        self.open_db(index=self.args.index)
        url_list = self.get_url_frame_info()

        for entry in entry_list:
            for url_info in url_list:
                url = url_info['url_frame'].format(query=entry['entry'])

                ex_list = self.trace_examples(url=url, meta=url_info['meta'])

                self.logger.log(level=self.MESSAGE, msg=LogMsg({
                    'message': 'saved',
                    'entry': entry['entry'],
                    'length': len(ex_list),
                    'ex_list': [ex for ex in ex_list[:5]]
                }))

                if len(ex_list) == 0:
                    break

                sleep(5)

            self.set_as_done(doc=entry)

        return

    def batch(self):
        """"""
        self.args = self.init_arguments()

        self.logger = self.get_logger()

        if self.args.remove_same_example is True:
            self.remove_same_example()
        elif 'reset_list' in self.args and self.args.reset_list is True:
            self.reset_list()
        else:
            self.trace_entry_list()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--lang', default='', help='')

        parser.add_argument('--columns', default='english,chinese', help='')

        parser.add_argument('--index', default='crawler-dictionary-example-youdao', help='')
        parser.add_argument('--list_index', default='crawler-dictionary-example-youdao-list', help='')

        parser.add_argument('--reset_list', action='store_true', default=False, help='')
        parser.add_argument('--remove_same_example', action='store_true', default=False, help='')

        return parser.parse_args()


if __name__ == '__main__':
    YoudaoExampleSearch().batch()
