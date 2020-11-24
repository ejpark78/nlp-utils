#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
from datetime import datetime
from time import sleep

import pytz
import requests
from bs4 import BeautifulSoup
from tqdm.autonotebook import tqdm

from utils import ElasticSearchUtils

MESSAGE = 25
logging_opt = {
    'format': '[%(levelname)-s] %(message)s',
    'handlers': [logging.StreamHandler()],
    'level': MESSAGE,

}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)


class LineageMBBSEng(object):
    """크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        host_info = {
            'host': 'https://corpus.ncsoft.com:9200',
            'index': 'crawler-bbs-game-bns-eng',
            'http_auth': 'crawler:crawler2019',
            'split_index': True,
        }

        self.elastic = ElasticSearchUtils(**host_info)

        self.timezone = pytz.timezone('Asia/Seoul')

    @staticmethod
    def get_forum_info():
        url = 'https://forums.bladeandsoul.com/en/'

        resp = requests.get(url, verify=False)

        soup = BeautifulSoup(resp.text, 'html5lib')

        result = []
        for forum in soup.select('ol li.cForumRow'):
            doc = {
                'forum_title': ''.join([v.get_text().strip() for v in forum.select('h4.ipsDataItem_title a')]),
                'forum_url': ''.join([v['href'] for v in forum.select('h4.ipsDataItem_title a')]),
            }

            result.append(doc)

        return result

    @staticmethod
    def get_forum_max_page(url):
        resp = requests.get(url, verify=False)
        soup = BeautifulSoup(resp.text, 'html5lib')

        tags = soup.select('ul.ipsPagination li.ipsPagination_last a')
        if len(tags) == 0 or tags[0].has_attr('data-page') is False:
            return 1

        return int(tags[0]['data-page'])

    @staticmethod
    def get_max_article(url):
        resp = requests.get(url, verify=False)
        soup = BeautifulSoup(resp.text, 'html5lib')

        tags = [v['data-page'] for v in soup.select('ul li.ipsPagination_last a') if v.has_attr('data-page')]
        if len(tags) > 0:
            return int(tags[0])

        return 1

    @staticmethod
    def get_articles(url):
        resp = requests.get(url, verify=False)
        soup = BeautifulSoup(resp.text, 'html5lib')

        result = []
        for article in soup.select('article'):
            tags = article.find_all('div', {'data-role': 'commentContent'})
            contents = tags[0]

            meta = article.find_all('div', {'data-controller': 'core.front.core.comment'})[0]

            doc = json.loads(meta['data-quotedata'])

            doc['content'] = contents.get_text().strip()
            doc['html_content'] = str(contents)
            doc['timestamp'] = datetime.fromtimestamp(doc['timestamp']).isoformat()

            result.append(doc)

        return result

    @staticmethod
    def get_forum_list(url, forum):
        resp = requests.get(url, verify=False)
        soup = BeautifulSoup(resp.text, 'html5lib')

        result = []
        for tag in soup.select('ol li.ipsDataItem'):
            if tag.has_attr('data-rowid') is False:
                continue

            stats = [v.get_text().strip() for v in tag.select(
                'ul.ipsDataItem_stats span.ipsDataItem_stats_number')]

            title_tags = [v for v in tag.select('h4.ipsDataItem_title a') if v.has_attr('data-ipshover-target')]
            if len(title_tags) == 0:
                continue

            doc = {
                'rowid': int(tag['data-rowid']),
                'title': title_tags[-1].get_text().strip(),
                'url': title_tags[-1]['href'],
                'author': ''.join([v.get_text().strip() for v in tag.select('div.ipsDataItem_meta a')]),
                'date': ''.join([v['datetime'] for v in tag.select('div.ipsDataItem_meta time')]),
                'replies': int(stats[0].replace(',', '')),
                'views': int(stats[1].replace(',', '')),
            }
            doc.update(forum)

            doc['_id'] = '{}-{}'.format(doc['forum_url'].strip('/').split('/')[-1], doc['rowid'])

            result.append(doc)

        return result

    def trace_articles(self, doc):
        max_page = self.get_max_article(url=doc['url'])
        sleep(3)

        articles = []
        for page in range(max_page + 1):
            url = '{url}/?page={page}'.format(url=doc['url'], page=page)

            articles += self.get_articles(url=url)
            sleep(3)

        doc['articles'] = articles
        return doc

    def trace_forum(self, forum):
        max_page = self.get_forum_max_page(forum['forum_url'])
        sleep(3)

        for page in tqdm(range(max_page + 1), desc='trace forum'):
            url = '{forum_url}/?page={page}&listResort=1'.format(
                forum_url=forum['forum_url'], page=page)

            doc_list = self.get_forum_list(url=url, forum=forum)

            for doc in doc_list:
                doc['curl_date'] = datetime.now(self.timezone).isoformat()
                self.elastic.save_document(document=doc, delete=False)

            self.elastic.flush()

            for doc in tqdm(doc_list, desc='trace article'):
                doc = self.trace_articles(doc=doc)

                doc['curl_date'] = datetime.now(self.timezone).isoformat()
                self.elastic.save_document(document=doc, delete=False)
                self.elastic.flush()

            sleep(3)

        return

    def batch(self):
        """"""
        forum_info = [
            {'forum_title': 'News and Announcements',
             'forum_url': 'https://forums.bladeandsoul.com/forum/412-news-and-announcements/'},
            {'forum_title': 'General Discussion',
             'forum_url': 'https://forums.bladeandsoul.com/forum/421-general-discussion/'},
            {'forum_title': 'PvE',
             'forum_url': 'https://forums.bladeandsoul.com/forum/423-pve/'},
            {'forum_title': 'PvP',
             'forum_url': 'https://forums.bladeandsoul.com/forum/430-pvp/'},
            {'forum_title': 'Fall Comic Contest Submissions',
             'forum_url': 'https://forums.bladeandsoul.com/forum/692-fall-comic-contest-submissions/'},
            {'forum_title': 'Esports',
             'forum_url': 'https://forums.bladeandsoul.com/forum/662-esports/'},
            {'forum_title': 'Player to Player Support',
             'forum_url': 'https://forums.bladeandsoul.com/forum/419-player-to-player-support/'},
            {'forum_title': 'Fan Creations',
             'forum_url': 'https://forums.bladeandsoul.com/forum/438-fan-creations/'},
            {'forum_title': 'Bug Reports',
             'forum_url': 'https://forums.bladeandsoul.com/forum/439-bug-reports/'},
            {'forum_title': 'Classes',
             'forum_url': 'https://forums.bladeandsoul.com/forum/631-classes/'},
            {'forum_title': 'Servers',
             'forum_url': 'https://forums.bladeandsoul.com/forum/440-servers/'}
        ]

        pbar = tqdm(forum_info)

        for forum in pbar:
            pbar.set_description(forum['forum_title'])
            self.trace_forum(forum=forum)

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-config', default='./naver.bbs.list.json', help='')
        parser.add_argument('-contents', action='store_true', default=False, help='')

        return parser.parse_args()


if __name__ == '__main__':
    LineageMBBSEng().batch()
