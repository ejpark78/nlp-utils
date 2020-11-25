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

from utils.dictionary_utils import DictionaryUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class EudicExampleSearch(DictionaryUtils):
    """사전 예문 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

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

    def trace_examples(self, url, post_data):
        """ """
        resp = requests.post(url=url, data=post_data, verify=False)

        soup = BeautifulSoup(resp.content, 'lxml')

        result = []
        for tag in soup.select('div.lj_item'):
            example = [t.get_text() for t in tag.select('p')]
            if len(example) == 0:
                example = ['', '']

            origin = ''
            lj_tag = tag.select_one('span.lj_origin')
            if lj_tag is not None:
                origin = lj_tag.get_text(' ')

            doc = {
                '_id': str(uuid4()),
                'data': unquote(tag['data']),
                'source': unquote(tag['source']),
                'original': origin,
                'english': example[0],
                'chinese': example[1],
            }

            self.elastic.save_document(document=doc, delete=False)
            result.append(doc)

        self.elastic.flush()

        return result

    @staticmethod
    def get_url_frame_info():
        """ """
        return {
            'status': 'http://dict.eudic.net/liju/en/{query}',
            'examples': [
                {
                    'url_frame': 'http://dict.eudic.net/dicts/LoadMoreLiju',
                    'post_data': {
                        'start': '{start}',
                        'status': '{status}',
                        'type': 'dict'
                    }
                },
                {
                    'url_frame': 'http://dict.eudic.net/dicts/LoadMoreLiju',
                    'post_data': {
                        'start': '{start}',
                        'status': '{status}',
                        'type': 'ting'
                    }
                }
            ]
        }

    def trace_entry_list(self):
        """ """
        entry_list = self.read_entry_list(lang=self.env.lang, column='state')

        self.open_db(index=self.env.index)
        url_frame_info = self.get_url_frame_info()

        for entry in entry_list:
            status = self.get_status_code(query=entry['entry'], url_frame=url_frame_info['status'])
            sleep(5)

            if status is None:
                continue

            for url_info in url_frame_info['examples']:
                post_data = url_info['post_data']

                for start in range(0, 100000, 20):
                    self.logger.log(msg={
                        'message': 'request',
                        'entry': entry['entry'],
                        'start': start,
                        'status': status,
                    })

                    post_data['start'] = start
                    post_data['status'] = status

                    ex_list = self.trace_examples(
                        url=url_info['url_frame'],
                        post_data=post_data,
                    )

                    self.logger.log(msg={
                        'message': 'saved',
                        'entry': entry['entry'],
                        'start': start,
                        'status': status,
                        'length': len(ex_list),
                        'ex_list': [{'english': ex['english'], 'chinese': ex['chinese']} for ex in ex_list[:5]]
                    })

                    if len(ex_list) == 0:
                        break

                    sleep(5)

            self.set_as_done(doc=entry, column='state')

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

        parser.add_argument('--columns', default='english,chinese', help='')

        parser.add_argument('--index', default='crawler-dictionary-example-eudic', help='')
        parser.add_argument('--list_index', default='crawler-dictionary-example-eudic-list', help='')

        return parser.parse_args()


if __name__ == '__main__':
    EudicExampleSearch().batch()
