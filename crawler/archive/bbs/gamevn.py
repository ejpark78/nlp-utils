#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
from datetime import datetime
from time import sleep
from urllib.parse import urljoin

import pytz
import requests
from bs4 import BeautifulSoup

from crawler.utils.elasticsearch import ElasticSearchUtils
from crawler.utils.logger import Logger


class ForumUtils(object):

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.logger = Logger()

        self.try_count = 0
        self.max_try = 3

    def request_html(self, url):
        """url에 대한 문서를 조회한다."""
        from requests.exceptions import ConnectionError

        resp = None
        try:
            resp = requests.get(url, verify=False)
        except ConnectionError:
            msg = {
                'level': 'ERROR',
                'message': 'ConnectionError',
                'url': url,
            }
            self.logger.error(msg=msg)

            if self.try_count < self.max_try:
                self.try_count += 1

                sleep(30)
                self.request_html(url=url)

        self.try_count = 0

        return resp

    def get_max_page(self, url, css, soup=None):
        """페이지네이션에서 최대 페이지수를 반환한다."""
        if soup is None:
            resp = self.request_html(url=url)
            if resp is None:
                return 1, None

            soup = BeautifulSoup(resp.content, 'html5lib')

        tags = [int(x.get_text()) for x in soup.select(css) if x.get_text().isdigit()]
        if len(tags) == 0:
            return 1, soup

        return max(tags), soup

    def get_topic_list(self, url, css):
        """ """
        resp = self.request_html(url=url)
        if resp is None:
            return []

        soup = BeautifulSoup(resp.content, 'html5lib')

        result = [urljoin(url, '/' + x['href']) for x in soup.select(css) if x.has_attr('href')]

        return result

    @staticmethod
    def get_html(soup, css):
        """ """
        return '\n'.join([str(x) for x in soup.select(css)]).strip()

    @staticmethod
    def get_text(soup, css):
        """soup 태그에서 텍스트를 추출한다."""
        return ''.join([x.get_text('\n') for x in soup.select(css)]).strip()

    @staticmethod
    def get_attr(soup, css, attr):
        """soup 태그에서 속성을 반환한다."""
        return ''.join([x[attr] for x in soup.select(css) if x.has_attr(attr)])


class GameVn(ForumUtils):

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.sleep = 5

        self.host_info = {
            'host': os.getenv('ELASTIC_SEARCH_HOST', 'https://corpus.ncsoft.com:9200'),
            'index': 'crawler-bbs-game-lineage-vi',
            'http_auth': 'crawler:crawler2019',
        }

        self.elastic = ElasticSearchUtils(**self.host_info)
        self.timezone = pytz.timezone('Asia/Seoul')

    def trace_topic(self, url_list, css_info):
        """ """
        for url_frame in url_list:
            max_page, soup = self.get_max_page(url=url_frame, css=css_info['page_nav'])

            topic = self.get_text(soup=soup, css='div.titleBar h1')

            for page in range(1, max_page + 1):
                url = f'{url_frame}page-{page}'

                msg = {
                    'level': 'MESSAGE',
                    'message': 'trace_topic',
                    'url': url,
                    'page': page,
                    'max_page': max_page,
                }
                self.logger.log(msg=msg)

                resp = self.request_html(url=url)
                if resp is None:
                    continue

                soup = BeautifulSoup(resp.content, 'html5lib')

                for item in soup.select('ol.messageList li'):
                    if item.has_attr('id') is False:
                        msg = {
                            'level': 'ERROR',
                            'message': 'missing doc id',
                            'url': url,
                            'item': str(item),
                        }
                        self.logger.error(msg=msg)
                        continue

                    doc = {
                        '_id': item['id'],
                        'topic': topic,
                        'date': self.get_attr(soup=item, css='div.messageMeta span.DateTime', attr='title'),
                        'username': self.get_text(soup=item, css='div.messageMeta a.username'),
                        'user_title': self.get_text(soup=item, css='em.userTitle'),
                        'contents': self.get_text(soup=item, css='article'),
                        'curl_date': datetime.now(self.timezone).isoformat(),
                        'html_content': str(item),
                    }

                    self.elastic.save_document(document=doc, delete=False)

                self.elastic.flush()

                sleep(self.sleep)

        return

    def trace_forum(self, forum):
        """ """
        css_info = {
            'page_nav': '#content div.PageNav nav a',
            'topic_list': 'ol li h3.title a',
        }

        max_page, _ = self.get_max_page(url=forum['url'].format(page=1), css=css_info['page_nav'])
        sleep(self.sleep)

        msg = {
            'level': 'MESSAGE',
            'message': 'trace_forum',
            'max_page': max_page,
            'forum': forum
        }
        self.logger.log(msg=msg)

        for page in range(max_page + 1):
            url = forum['url'].format(page=page)

            url_list = self.get_topic_list(url=url, css=css_info['topic_list'])

            self.trace_topic(url_list=url_list, css_info=css_info)

            sleep(self.sleep)

        return

    def batch(self):
        """"""
        forum_info = [
            {
                'url': 'http://forum.gamevn.com/forums/lineage-2.217/page-{page}',
                'meta': {
                    'category': 'Lineage 2',
                    'title': 'Lineage 2',
                }
            },
            {
                'url': 'http://forum.gamevn.com/forums/mua-ban.233/page-{page}',
                'meta': {
                    'category': 'Lineage 2',
                    'title': 'Mua bán',
                }
            },
            {
                'url': 'http://forum.gamevn.com/forums/l2s-third-party.234/page-{page}',
                'meta': {
                    'category': 'Lineage 2',
                    'title': 'L2\'s Third Party',
                }
            }
        ]

        for forum in forum_info:
            self.trace_forum(forum=forum)

        return


if __name__ == '__main__':
    GameVn().batch()
