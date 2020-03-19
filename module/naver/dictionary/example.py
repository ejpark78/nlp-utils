#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
from time import sleep

import pandas as pd
import requests
import urllib3
from tqdm.autonotebook import tqdm

from module.dictionary_utils import DictionaryUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ExampleCrawler(DictionaryUtils):
    """사전 예문 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

    def trace_example(self, index, keyword, sleep_time):
        """"""
        p_bar = None

        query = {
            'page': 1,
            'query': keyword,
            'domain': 'https://en.dict.naver.com/api3/enko/search',
            'common_query': 'm=pc&range=example&lang=ko&shouldSearchVlive=false',
        }

        headers = {
            'Referer': 'https://en.dict.naver.com/'
        }
        headers.update(self.headers)

        total = -1
        max_page = 10

        while query['page'] < max_page:
            url = '{domain}?query={query}&page={page}&{common_query}'.format(**query)

            try:
                resp = requests.get(url=url, headers=headers).json()
            except Exception as e:
                query['page'] += 1

                print(e)
                continue

            items = resp['searchResultMap']['searchResultListMap']['EXAMPLE']['items']
            if total < 0:
                total = resp['searchResultMap']['searchResultListMap']['EXAMPLE']['total']
                max_page = resp['pagerInfo']['totalPages']

                p_bar = tqdm(
                    total=max_page,
                    desc='{}: {:,}'.format(keyword, total),
                    dynamic_ncols=True
                )

            p_bar.update(1)

            # 저장
            for doc in items:
                doc['query'] = keyword

                doc['expExample1'] = re.sub('<strong>(.+?)</strong>', '\g<1>', doc['expExample1'])
                doc['expExample2'] = re.sub('<strong>(.+?)</strong>', '\g<1>', doc['expExample2'])

                self.elastic.save_document(index=index, document=doc, delete=False)

            self.elastic.flush()

            query['page'] += 1
            if max_page < query['page']:
                break

            sleep(sleep_time)

        return

    @staticmethod
    def get_entry_list(elastic, index, rank):
        """"""
        query = {
            '_source': [
                'document_id',
                'entry'
            ],
            'query': {
                'bool': {
                    'must': [
                        {
                            'match': {
                                'rank': rank
                            }
                        }
                    ],
                    'must_not': [
                        {
                            'match': {
                                'state': 'done'
                            }
                        }
                    ]
                }
            }
        }

        entry_list = []
        elastic.export(index=index, query=query, result=entry_list)

        return pd.DataFrame(entry_list)

    def batch(self):
        """"""
        index = {
            'entry_list': 'crawler-naver-dictionary',
            'example': 'crawler-naver-dictionary-example',
        }

        self.open_db(index=index['entry_list'])

        # entry_list = get_entry_list(elastic=utils, index=index['entry_list'], rank='매우 중요 단어')
        entry_list = self.get_entry_list(index=index['entry_list'], rank='중요 단어')
        entry_list.head()

        print(len(entry_list))

        for i, row in tqdm(entry_list.iterrows(), total=len(entry_list)):
            self.trace_example(
                index=index['example'],
                keyword=row['entry'],
                sleep_time=10,
            )

            self.elastic.save_document(
                index=index['entry_list'],
                document={'_id': row['document_id'], 'state': 'done'},
                delete=False
            )
            self.elastic.flush()

        return

    def daum(self):
        """
url = 'https://dic.daum.net/search_more.do?q=love&dic=eng&t=example&page=1'

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
    'Referer': 'https://dic.daum.net/search.do?q=love&dic=eng&search_first=Y'
}

daum = requests.get(url=url, headers=headers)
daum

daum.content

from bs4 import BeautifulSoup

soup = BeautifulSoup(daum.content, 'lxml')
soup.prettify()

        :return:
        """

        return


if __name__ == '__main__':
    ExampleCrawler().batch()
