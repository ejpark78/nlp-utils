#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep
from urllib.parse import urlencode
from uuid import uuid4
from bs4 import BeautifulSoup

import requests
import urllib3

from module.dictionary_utils import DictionaryUtils
from module.utils.logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ExampleSearchCrawler(DictionaryUtils):
    """사전 예문 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

    def trace_examples(self, url, query, lang):
        """ """
        url = '{}?{}'.format(url, urlencode(query))

        resp = requests.get(url=url, verify=False).json()

        result = []
        for doc in resp['exampleList']:
            doc['_id'] = str(uuid4())
            doc['translationDirection'] = lang

            soup = BeautifulSoup(doc['translation'], 'html5lib')
            doc['translationText'] = soup.get_text()

            if self.is_skip(doc=doc, columns=['example', 'translationText']) is True:
                continue

            self.elastic.save_document(document=doc, delete=False)
            result.append(doc)

        self.elastic.flush()

        return result

    @staticmethod
    def get_url_frame_info():
        """ """
        return {
            'cn-en': {
                'method': 'GET',
                'url_frame': 'https://dict.naver.com/linedict/cnen/example/search.dict',
                'query': {
                    'query': '',
                    'page': 1,
                    'page_size': 100,
                    'examType': 'normal',
                    'fieldType': '',
                    'author': '',
                    'country': '',
                    'ql': 'default',
                    'format': 'json',
                    'platform': 'isPC',
                }
            },
            'en-cn': {
                'method': 'GET',
                'url_frame': 'https://dict.naver.com/linedict/encn/example/search.dict',
                'query': {
                    'query': '',
                    'page': 1,
                    'page_size': 100,
                    'examType': 'normal',
                    'fieldType': '',
                    'author': '',
                    'country': '',
                    'ql': 'default',
                    'format': 'json',
                    'platform': 'isPC',
                }
            }
        }

    def trace_entry_list(self):
        """ """
        entry_list = self.read_entry_list()

        self.open_db(index=self.args.index)
        url_frame = self.get_url_frame_info()

        for entry in entry_list:
            for lang in url_frame:
                url_info = url_frame[lang]

                self.skip = 0
                self.cache.clear()

                for page in range(1, 500):
                    query = url_info['query']

                    query['page'] = page
                    query['query'] = entry['entry']

                    self.logger.log(level=self.MESSAGE, msg=LogMsg({
                        'message': '예문 조회',
                        'entry': entry['entry'],
                        'page': page,
                        'lang': lang,
                        'query': query,
                    }))

                    ex_list = self.trace_examples(url=url_info['url_frame'], query=query, lang=lang)

                    self.logger.log(level=self.MESSAGE, msg=LogMsg({
                        'message': '저장 성공',
                        'entry': entry['entry'],
                        'lang': lang,
                        'page': page,
                        'skip': self.skip,
                        'length': len(ex_list),
                        'ex_list': [{x['example'], x['translationText']} for x in ex_list[:10]],
                    }))

                    if self.skip >= len(ex_list):
                        break

                    sleep(7)

            self.set_as_done(doc=entry)

        return

    def batch(self):
        """"""
        self.args = self.init_arguments()

        self.logger = self.get_logger()

        if 'remove_same_example' in self.args and self.args.remove_same_example is True:
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

        parser.add_argument('--index', default='crawler-dictionary-example-linedict', help='')
        parser.add_argument('--list_index', default='crawler-dictionary-example-linedict-list', help='')

        parser.add_argument('--columns', default='example,translationText', help='')

        parser.add_argument('--reset_list', action='store_true', default=False, help='')
        parser.add_argument('--remove_same_example', action='store_true', default=False, help='')

        return parser.parse_args()


if __name__ == '__main__':
    ExampleSearchCrawler().batch()
