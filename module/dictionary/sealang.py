#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from time import sleep
from uuid import uuid4

import requests
import urllib3
from bs4 import BeautifulSoup

from module.dictionary_utils import DictionaryUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SealangExampleSearch(DictionaryUtils):
    """사전 예문 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.url_frame_info = {
            'vien': [
                {
                    'url': 'http://sealang.net/pm/bitext.pl',
                    'post_data': {
                        'type': 'bitext',
                        'seaLanguage': 'vietnamese',
                        'return': 'html',
                        'seaTarget': '',
                        'switcher': 'OFF',
                        'westernTarget': '',
                        'near': '10',
                        'bitextMatch': 'or',
                        'approx': 'W',
                        'westernLanguage': 'english',
                    }
                }
            ],
            'iden': [
                {
                    'url': 'http://sealang.net/pm/bitext.pl',
                    'post_data': {
                        'type': 'bitext',
                        'seaLanguage': 'indonesia',
                        'return': 'html',
                        'seaTarget': '',
                        'switcher': 'OFF',
                        'westernTarget': '',
                        'near': '10',
                        'bitextMatch': 'or',
                        'approx': 'W',
                        'westernLanguage': 'english',
                    }
                }
            ],
            'then': [
                {
                    'url': 'http://sealang.net/pm/bitext.pl',
                    'post_data': {
                        'type': 'bitext',
                        'seaLanguage': 'thai',
                        'return': 'html',
                        'seaTarget': '',
                        'switcher': 'OFF',
                        'westernTarget': '',
                        'near': '10',
                        'bitextMatch': 'or',
                        'approx': 'W',
                        'westernLanguage': 'english',
                    }
                }
            ]
        }

    def trace_examples(self, url, post_data):
        """ """
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/81.0.4044.113 '
                          'Safari/537.36',
            'Referer': 'http://sealang.net/vietnamese/bitext-top.htm',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'http://sealang.net',
            'Host': 'sealang.net',
            'Accept': 'text/html,application/xhtml+xml,'
                      'application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,'
                      'application/signed-exchange;v=b3;q=0.9',
            'Upgrade-Insecure-Requests': '1'
        }

        column = {
            'source': self.env.source_column,
            'target': self.env.target_column,
        }

        resp = requests.post(url=url, data=post_data, headers=headers, verify=False)

        soup = BeautifulSoup(resp.content, 'lxml')

        result = []
        for tag in soup.select('ltab'):
            example = [t.get_text().strip() for t in tag.select('row')]
            if len(example) == 0:
                example = ['', '']

            doc = {
                '_id': str(uuid4()),
                column['source']: example[0],
                column['target']: example[1],
            }

            self.elastic.save_document(document=doc, delete=False)
            result.append(doc)

        self.elastic.flush()

        return result

    def trace_entry_list(self):
        """ """
        entry_list = self.read_entry_list(lang=self.env.search_lang, column=self.env.state_column)

        self.open_db(index=self.env.index)

        for entry in entry_list:
            if 'entry' not in entry:
                continue

            for url_info in self.url_frame_info[self.env.lang]:
                post_data = json.loads(json.dumps(url_info['post_data']))

                if entry['lang'] == 'en' or entry['lang'] == 'fr':
                    post_data['westernTarget'] = entry['entry']
                else:
                    post_data['seaTarget'] = entry['entry']

                ex_list = self.trace_examples(url=url_info['url'], post_data=post_data)

                self.logger.log(msg={
                    'message': 'saved',
                    'entry': entry['entry'],
                    'length': len(ex_list),
                    'ex_list': [ex for ex in ex_list[:5]]
                })

                if len(ex_list) == 0:
                    break

                sleep(self.env.sleep)

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

        parser.add_argument('--lang', default='vien')
        parser.add_argument('--search_lang', default='en,vi')

        parser.add_argument('--columns', default='vietnamese,english')
        parser.add_argument('--source_column', default='vietnamese')
        parser.add_argument('--target_column', default='english')
        parser.add_argument('--state_column', default='state_sealang_vien')

        parser.add_argument('--index', default='crawler-dictionary-example-sealang-vien')
        parser.add_argument('--list_index', default='crawler-dictionary-example-word-list')

        parser.add_argument('--sleep', default=25, type=int)

        return parser.parse_args()


if __name__ == '__main__':
    SealangExampleSearch().batch()
