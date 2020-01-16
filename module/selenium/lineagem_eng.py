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

from module.elasticsearch_utils import ElasticSearchUtils

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
            'index': 'crawler-bbs-game-multilingual',
            'http_auth': 'crawler:crawler2019',
            'split_index': True,
        }

        self.elastic = ElasticSearchUtils(**host_info)

        self.timezone = pytz.timezone('Asia/Seoul')

    @staticmethod
    def get_forum_info():
        url = 'https://forums.lineage2.com/'

        resp = requests.get(url)

        soup = BeautifulSoup(resp.text, 'html5lib')

        result = []
        for forum in soup.select('ol.cForumList li'):
            category = ''.join([v.get_text().strip() for v in forum.select('h2.cForumTitle a')])

            for tag in forum.select('ol li.ipsDataItem'):
                stats = [v.get_text().strip() for v in tag.select('ul.ipsDataItem_stats span.ipsDataItem_stats_number')]

                doc = {
                    'category': category,
                    'forum_title': ''.join([v.get_text().strip() for v in tag.select('h4 a')]),
                    'forum_url': ''.join([v['href'] for v in tag.select('h4 a')]),
                }

                result.append(doc)

        return result

    @staticmethod
    def get_forum_max_page(url):
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html5lib')

        tags = soup.select('ul.ipsPagination li.ipsPagination_last a')
        if len(tags) == 0 or tags[0].has_attr('data-page') is False:
            return 1

        return int(tags[0]['data-page'])

    @staticmethod
    def get_max_article(url):
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html5lib')

        tags = [v['data-page'] for v in soup.select('ul li.ipsPagination_last a') if v.has_attr('data-page')]
        if len(tags) > 0:
            return int(tags[0])

        return 1

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-config', default='./naver.bbs.list.json', help='')
        parser.add_argument('-contents', action='store_true', default=False, help='')

        return parser.parse_args()

    @staticmethod
    def get_articles(url):
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html5lib')

        result = []
        for article in soup.select('article'):
            tags = article.find_all('div', {'data-role': 'commentContent'})
            contents = tags[0]

            meta = article.find_all('div', {'data-controller': 'core.front.core.comment'})[0]

            doc = json.loads(meta['data-quotedata'])

            doc['content'] = contents.get_text().strip()
            doc['timestamp'] = datetime.fromtimestamp(doc['timestamp']).isoformat()

            result.append(doc)

        return result

    @staticmethod
    def get_forum_list(url, forum):
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html5lib')

        result = []
        for tag in soup.select('ol li.ipsDataItem'):
            stats = [v.get_text().strip() for v in tag.select(
                'ul.ipsDataItem_stats span.ipsDataItem_stats_number')]

            title = tag.select('h4.ipsDataItem_title a')[0]
            if tag.has_attr('data-rowid') is False:
                continue

            doc = {
                'rowid': int(tag['data-rowid']),
                'title': title.get_text().strip(),
                'url': title['href'],
                'author': ''.join([v.get_text().strip() for v in tag.select('div.ipsDataItem_meta a')]),
                'date': ''.join([v['datetime'] for v in tag.select('div.ipsDataItem_meta time')]),
                'replies': int(stats[0]),
                'views': int(stats[1]),
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


def main():
    """"""
    utils = LineageMBBSEng()

    # forum_info = get_forum_info()
    forum_info = [
        #     {'category': 'Lineage II',
        #      'forum_title': 'General Live Discussion',
        #      'forum_url': 'https://forums.lineage2.com/forum/4-general-live-discussion/'},
        # {'category': 'Lineage II',
        #  'forum_title': 'Game Questions',
        #  'forum_url': 'https://forums.lineage2.com/forum/5-game-questions/'},
        # {'category': 'Lineage II',
        #  'forum_title': 'Future Updates Discussion',
        #  'forum_url': 'https://forums.lineage2.com/forum/33-future-updates-discussion/'},
        # {'category': 'Lineage II',
        #  'forum_title': 'Server Discussions',
        #  'forum_url': 'https://forums.lineage2.com/forum/6-server-discussions/'},
        # {'category': 'Lineage II',
        #  'forum_title': 'Classes Discussion',
        #  'forum_url': 'https://forums.lineage2.com/forum/16-classes-discussion/'},
        {'category': 'Lineage II',
         'forum_title': 'Player to Player Support',
         'forum_url': 'https://forums.lineage2.com/forum/24-player-to-player-support/'},
        {'category': 'Lineage II',
         'forum_title': 'Report A Bug',
         'forum_url': 'https://forums.lineage2.com/forum/27-report-a-bug/'},
        {'category': 'Lineage II',
         'forum_title': 'Fan Creation',
         'forum_url': 'https://forums.lineage2.com/forum/25-fan-creation/'},
        {'category': 'Lineage II',
         'forum_title': 'Suggestion Box',
         'forum_url': 'https://forums.lineage2.com/forum/29-suggestion-box/'},
        {'category': 'Lineage II',
         'forum_title': 'Archive',
         'forum_url': 'https://forums.lineage2.com/forum/30-archive/'},
        {'category': 'Classic',
         'forum_title': 'General Classic Discussion',
         'forum_url': 'https://forums.lineage2.com/forum/35-general-classic-discussion/'},
        {'category': 'Classic',
         'forum_title': 'Game Questions',
         'forum_url': 'https://forums.lineage2.com/forum/49-game-questions/'},
        {'category': 'Classic',
         'forum_title': 'Fan Creations',
         'forum_url': 'https://forums.lineage2.com/forum/53-fan-creations/'},
        {'category': 'Classic',
         'forum_title': 'Server Discussions',
         'forum_url': 'https://forums.lineage2.com/forum/41-server-discussions/'},
        {'category': 'Classic',
         'forum_title': 'Race & Classes Discussion',
         'forum_url': 'https://forums.lineage2.com/forum/40-race-classes-discussion/'},
        {'category': 'Classic',
         'forum_title': 'Clan Recruitment',
         'forum_url': 'https://forums.lineage2.com/forum/39-clan-recruitment/'},
        {'category': 'Classic',
         'forum_title': 'Player to Player Support',
         'forum_url': 'https://forums.lineage2.com/forum/36-player-to-player-support/'},
        {'category': 'Classic',
         'forum_title': 'Report A Bug',
         'forum_url': 'https://forums.lineage2.com/forum/37-report-a-bug/'},
        {'category': 'Classic',
         'forum_title': 'Archive',
         'forum_url': 'https://forums.lineage2.com/forum/38-archive/'}
    ]

    pbar = tqdm(forum_info)

    for forum in pbar:
        pbar.set_description(forum['forum_title'])
        utils.trace_forum(forum=forum)

    return


if __name__ == '__main__':
    main()
