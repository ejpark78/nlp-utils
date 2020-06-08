#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from datetime import datetime
from time import sleep
from urllib.parse import urljoin

import pytz
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from tqdm.autonotebook import tqdm
import xmltodict
import json
from module.utils.elasticsearch_utils import ElasticSearchUtils

MESSAGE = 25
logging_opt = {
    'format': '[%(levelname)-s] %(message)s',
    'handlers': [logging.StreamHandler()],
    'level': MESSAGE,

}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)


class ForumUtils(object):

    def __init__(self):
        """ 생성자 """
        super().__init__()

    @staticmethod
    def get_max_page(url, css, soup=None):
        """ """
        if soup is None:
            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, 'html5lib')

        tags = [int(x.get_text()) for x in soup.select(css) if x.get_text().isdigit()]

        return max(tags)

    @staticmethod
    def get_topic_list(url, css):
        """ """
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html5lib')

        result = [urljoin(url, '/' + x['href']) for x in soup.select(css) if x.has_attr('href')]

        return result

    def trace_topic(self, url_list, css):
        """ """
        for url in url_list:
            max_page = self.get_max_page(url=url, css=css['page_nav'])

            for page in range(max_page + 1):

                pass

        return


class GameVn(ForumUtils):

    def __init__(self):
        """ 생성자 """
        super().__init__()

        host_info = {
            'host': 'https://corpus.ncsoft.com:9200',
            'index': 'crawler-bbs-game-lineage-vi',
            'http_auth': 'crawler:crawler2019',
            'split_index': True,
        }

        self.elastic = ElasticSearchUtils(**host_info)

        self.timezone = pytz.timezone('Asia/Seoul')

        self.sleep = 3

    def trace_forum(self, forum):
        """ """
        css = {
            'page_nav': '#content div.PageNav nav a',
            'topic_list': 'ol li h3.title a'
        }

        max_page = self.get_max_page(url=forum['url'].format(page=1), css=css['page_nav'])
        sleep(self.sleep)

        for page in range(max_page + 1):
            url = forum['url'].format(page=page)

            url_list = self.get_topic_list(url=url, css=css['topic_list'])

            self.trace_topic(url_list=url_list, css=css)

            # for doc in url_list:
            #     doc['curl_date'] = datetime.now(self.timezone).isoformat()
            #     self.elastic.save_document(document=doc, delete=False)

        #     self.elastic.flush()
        #
        #     for doc in tqdm(doc_list, desc='trace article'):
        #         doc = self.trace_articles(doc=doc)
        #
        #         doc['curl_date'] = datetime.now(self.timezone).isoformat()
        #         self.elastic.save_document(document=doc, delete=False)
        #         self.elastic.flush()
        #
        #     sleep(self.sleep)

        return

    def batch(self):
        """"""
        forum_info = [
            {
                'category': 'Lineage 2',
                'title': 'Lineage 2',
                'url': 'http://forum.gamevn.com/forums/lineage-2.217/page-{page}'
            },
            {
                'category': 'Lineage 2',
                'title': 'Mua bán',
                'url': 'http://forum.gamevn.com/forums/mua-ban.233/page-{page}'
            },
            {
                'category': 'Lineage 2',
                'title': 'L2\'s Third Party',
                'url': 'http://forum.gamevn.com/forums/l2s-third-party.234/page-{page}'
            }
        ]

        for forum in forum_info:
            self.trace_forum(forum=forum)

        return


def main():
    """"""
    utils = GameVn()
    utils.batch()

    return


if __name__ == '__main__':
    main()
