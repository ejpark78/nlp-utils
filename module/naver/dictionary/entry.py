#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import re
import sys
from math import ceil
from time import sleep
from uuid import uuid4

import requests
import urllib3
from bs4 import BeautifulSoup
from tqdm.autonotebook import tqdm
from urllib.parse import urljoin, urlencode

from module.naver.dictionary.utils import DictionaryUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MESSAGE = 25

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(format='%(message)s')

logger = logging.getLogger()

logger.setLevel(MESSAGE)
logger.handlers = [logging.StreamHandler(sys.stderr)]


class DictionaryEntryCrawler(DictionaryUtils):
    """사전 엔트리 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

    def get_entry_list(self, url, result, lang):
        """ """
        headers = {
            'Referer': url
        }
        headers.update(self.headers)

        resp = requests.get(url, headers=headers, timeout=60)

        soup = BeautifulSoup(resp.content, 'html5lib')

        total_tag = soup.find('div', {'class': 'word_list'})
        total_tag = total_tag.find('span', {'class': 'fnt_k17'})

        total = 1
        if total_tag is not None:
            total_text = total_tag.get_text()
            total_text = total_text.replace('건', '')

            total = int(total_text)

        entry_soup = soup.find('div', {'class': 'entrylist'})

        if lang == '중한':
            if entry_soup is not None:
                self.parse_zh(url=url, soup=entry_soup, result=result)
            else:
                entry_soup = soup.find('div', {'id': 'wordlist'})
                self.parse_zh_word_list(url=url, soup=entry_soup, result=result)

        if lang == '영한':
            self.parse_en(url=url, soup=entry_soup, result=result)

        return total

    @staticmethod
    def parse_zh(url, soup, result):
        """ """
        title = ['pos', 'definition', 'hsk_rank']
        for tr in soup.find_all('tr'):
            buf = []
            item = {}
            for tag in tr.find_all('td'):
                if 'link' not in item:
                    link = [x['href'] for x in tag.find_all('a') if x.has_attr('href')]
                    item['link'] = urljoin(url, link[0])

                    item['sound'] = ''.join([x.get_text() for x in tag.find_all('span')])
                    continue

                buf.append(tag.get_text().strip())

            if len(item) == 0:
                continue

            item.update(dict(zip(title, buf)))
            result.append(item)

        return

    @staticmethod
    def parse_zh_word_list(url, soup, result):
        """ """
        item = {}
        for tag in soup.select('li'):
            link = [x['href'] for x in tag.find_all('a') if x.has_attr('href')]
            item['link'] = urljoin(url, link[0])

            item['sound'] = ''.join([x.get_text() for x in tag.find_all('span')])

            if len(item) == 0:
                continue

            result.append(item)

        return

    @staticmethod
    def parse_en(url, soup, result):
        """ """
        for tr in soup.find_all('tr'):
            item = {}
            for tag in tr.find_all('td'):
                if tag.has_attr('class') is False:
                    continue

                text = tag.get_text()
                text = text.strip().replace('성우 발음듣기 정지', '')
                text = re.sub(r'\s+(\n|\t)', '\n', text)
                text = re.sub(r'(\n|\r|\t)+', '\n', text).strip()

                k = tag['class'][0]
                if k == 'f_name':
                    link_tag = tag.find('a')
                    if link_tag is None:
                        continue

                    item['link'] = urljoin(url, link_tag['href'])
                    item['entry'] = text.split('\n')[0]
                    item['sound'] = text.split('\n', maxsplit=2)[-1]
                elif k == 'f_con':
                    item[k] = text
                    item[k + '_html'] = str(tag)
                elif k == 'f_high':
                    if tag.has_attr('img') and tag.img.has_attr('title'):
                        item[k] = tag.img.title
                elif k == 'f_add':
                    continue
                else:
                    item[k] = text

            if len(item) == 0:
                continue

            result.append(item)

        return

    def trace_entry_list(self, query, sleep_time, index):
        """ """
        page = 1
        max_page = 10
        total = -1

        p_bar = None
        while page < max_page:
            url = '{site}?{query}&pageNo={page}'.format(
                site=query['site'],
                query=urlencode(query['query']),
                page=page,
            )

            data_list = []
            count = self.get_entry_list(url=url, result=data_list, lang=query['category'])

            if total < 0 < len(data_list):
                total = count
                max_page = ceil(total / len(data_list))
                p_bar = tqdm(total=max_page, dynamic_ncols=True)

            p_bar.update(1)

            # 저장
            common = self.parse_url(url)
            for doc in data_list:
                doc.update(common)

                if 'link' in doc:
                    doc.update(self.parse_url(doc['link']))

                doc['_id'] = str(uuid4())
                if 'entryId' in doc:
                    doc['_id'] = doc['entryId']
                elif 'entryID' in doc:
                    doc['_id'] = doc['entryID']
                elif 'idiomId' in doc:
                    doc['_id'] = 'idiom-' + doc['idiomId']
                else:
                    print(doc)

                if 'category' in query:
                    doc['category'] = query['category']

                self.elastic.save_document(index=index, document=doc, delete=False)

            self.elastic.flush()

            page += 1
            if page > max_page:
                break

            sleep(sleep_time)

        return

    def batch(self):
        """"""
        self.args = self.init_arguments()

        query_list = self.read_config(self.args.config)

        index = 'crawler-naver-dictionary'
        self.open_db(index=index)

        for query in tqdm(query_list):
            self.trace_entry_list(
                index=index,
                query=query,
                sleep_time=10,
            )

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        # parser.add_argument('--config', default='config/naver/dictionary/zh-ko.json', help='')
        parser.add_argument('--config', default='config/naver/dictionary/en-ko.json', help='')

        return parser.parse_args()


if __name__ == '__main__':
    DictionaryEntryCrawler().batch()
