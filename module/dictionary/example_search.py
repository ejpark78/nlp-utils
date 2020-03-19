#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep
from uuid import uuid4

import requests
import urllib3
from bs4 import BeautifulSoup

from module.dictionary_utils import DictionaryUtils
from module.utils.logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ExampleSearchCrawler(DictionaryUtils):
    """사전 예문 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

    @staticmethod
    def read_entry_list(filename):
        """설정파일을 읽어드린다."""
        import json

        result = []
        with open(filename, 'r') as fp:
            for line in fp.readlines():
                line = line.rstrip()
                if line.strip() == '' or line[0:2] == '//' or line[0] == '#':
                    continue

                result.append(json.loads(line))

        return result

    @staticmethod
    def get_status_code(query, url_frame):
        """ """
        url = url_frame.format(query=query)

        resp = requests.get(url)

        soup = BeautifulSoup(resp.content, 'lxml')

        status_code = soup.select_one('input#page-status')

        return status_code['value']

    def trace_examples(self, url, post_data):
        """ """
        from urllib.parse import unquote

        resp = requests.post(url=url, data=post_data)

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

    def batch(self):
        """"""
        logger = self.get_logger()

        index = 'crawler-dictionary-example'
        self.open_db(index=index)

        entry_list = self.read_entry_list('config/dict_example/eng-entry.list.json')

        url_frame_info = {
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

        for entry in entry_list:
            status = self.get_status_code(query=entry['entry'], url_frame=url_frame_info['status'])
            sleep(5)

            for url_info in url_frame_info['examples']:
                post_data = url_info['post_data']

                for start in range(0, 100000, 20):
                    logger.log(level=self.MESSAGE, msg=LogMsg({
                        'message': 'request',
                        'entry': entry['entry'],
                        'start': start,
                        'status': status,
                    }))

                    post_data['start'] = start
                    post_data['status'] = status

                    ex_list = self.trace_examples(
                        url=url_info['url_frame'],
                        post_data=post_data,
                    )

                    logger.log(level=self.MESSAGE, msg=LogMsg({
                        'message': 'saved',
                        'entry': entry['entry'],
                        'start': start,
                        'status': status,
                        'length': len(ex_list),
                        'ex_list': [{'english': ex['english'], 'chinese': ex['chinese']} for ex in ex_list[:5]]
                    }))

                    if len(ex_list) == 0:
                        break

                    sleep(5)

        return


if __name__ == '__main__':
    ExampleSearchCrawler().batch()
