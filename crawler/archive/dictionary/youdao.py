#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep
from uuid import uuid4

import re

import requests
import urllib3
from bs4 import BeautifulSoup

from crawler.utils.dictionary_utils import DictionaryUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class YoudaoSearch(DictionaryUtils):
    """사전 예문 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.url_frame_info = {
            'zhfr': [
                {
                    'url_frame': 'http://www.youdao.com/example/blng/fr/{query}/',
                    'meta': {
                        'category': 'all'
                    },
                }
            ],
            'zhja': [
                {
                    'url_frame': 'http://www.youdao.com/example/blng/jap/{query}/',
                    'meta': {
                        'category': 'all'
                    },
                }
            ],
            'zhko': [
                {
                    'url_frame': 'http://www.youdao.com/example/blng/ko/{query}/',
                    'meta': {
                        'category': 'all'
                    },
                }
            ],
            'enzh': [
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
                }
            ]
        }

    def get_status_code(self, query, url_frame):
        """ """
        url = url_frame.format(query=query)

        resp = requests.get(url, verify=False)

        soup = BeautifulSoup(resp.content, 'lxml')

        status_code = soup.select_one('input#page-status')
        if status_code is None or status_code.has_attr('value') is False:
            self.logger.error(msg={
                'message': 'status 조회 에러',
                'url': url,
            })
            return None

        return status_code['value']

    def trace_examples(self, url, meta):
        """ """
        column = {
            'source': self.env.source_column,
            'target': self.env.target_column,
        }

        resp = requests.get(url=url, verify=False)

        soup = BeautifulSoup(resp.content, 'lxml')

        result = []
        for tag in soup.select('div#bilingual ul li'):
            example = [t.get_text().strip() for t in tag.select('p')]
            if len(example) == 0:
                example = ['', '']

            doc = {
                '_id': str(uuid4()),
                'source': example[2],
                column['source']: example[0],
                column['target']: example[1],
            }
            doc.update(meta)

            if column['source'] == 'english':
                flag = re.findall(r'[\u4e00-\u9fff]+', doc[column['source']])
                if len(flag) != 0:
                    doc[column['target']] = example[0]
                    doc[column['source']] = example[1]

            self.elastic.save_document(document=doc, delete=False)
            result.append(doc)

        self.elastic.flush()

        return result

    def trace_entry_list(self):
        """ """
        entry_list = self.read_entry_list(lang=self.env.search_lang, column=self.env.state_column)

        self.open_db(index=self.env.index)

        for entry in entry_list:
            for url_info in self.url_frame_info[self.env.lang]:
                if 'entry' not in entry:
                    continue

                url = url_info['url_frame'].format(query=entry['entry'])

                ex_list = self.trace_examples(url=url, meta=url_info['meta'])

                self.logger.log(msg={
                    'message': 'saved',
                    'entry': entry['entry'],
                    'length': len(ex_list),
                    'ex_list': [ex for ex in ex_list[:5]]
                })

                if len(ex_list) == 0:
                    break

                sleep(5)

            self.set_as_done(doc=entry, column=self.env.state_column)

        return

    def batch(self):
        """"""
        self.env = self.init_arguments()

        if self.env.remove_same_example is True:
            self.remove_same_example()
        elif 'reset_list' in self.env and self.env.reset_list is True:
            self.reset_list(column='state')
        else:
            self.trace_entry_list()

        return

    def init_arguments(self):
        """ 옵션 설정 """
        parser = super().init_arguments()

        parser.add_argument('--lang', default='', help='')
        parser.add_argument('--search_lang', default='', help='')

        parser.add_argument('--columns', default='english,chinese', help='')
        parser.add_argument('--source_column', default='english', help='')
        parser.add_argument('--target_column', default='chinese', help='')
        parser.add_argument('--state_column', default='state_youdao', help='')

        parser.add_argument('--index', default='crawler-dictionary-example-youdao', help='')
        parser.add_argument('--list_index', default='crawler-dictionary-example-youdao-list', help='')

        return parser.parse_args()


if __name__ == '__main__':
    YoudaoSearch().batch()
