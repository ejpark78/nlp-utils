#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
from time import sleep
from urllib.parse import urljoin
from uuid import uuid4

import pytz
import requests
import urllib3
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError

from module.utils.elasticsearch_utils import ElasticSearchUtils
from module.utils.logger import Logger

urllib3.disable_warnings(UserWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GlosbeCrawler(object):
    """사전 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.env = None
        self.elastic = None

        self.MESSAGE = 25
        self.logger = Logger()

        self.session = requests.Session()
        self.session.verify = False

        self.base_url = 'https://glosbe.com'

        self.login_info = {
            'returnUrl': 'http://glosbe.com/loginRedirectInternal'
        }

        self.history = set()
        self.word_list = {}

    def open_db(self, index):
        """ """
        self.elastic = ElasticSearchUtils(host=self.env.host, http_auth=self.env.auth, index=index)
        return self.elastic

    def login(self):
        """ """
        login_url = 'https://auth2.glosbe.com/login'
        return self.session.post(login_url, data=self.login_info, timeout=120)

    def parse_word_list(self, soup):
        """ """
        word_list = {}
        for item in soup.select('#wordListContainer li a'):
            k = urljoin(self.base_url, item['href'])
            v = item.get_text()

            if k in self.word_list:
                continue

            word_list[k] = {
                'entry': v,
                'document_id': str(uuid4()),
            }

        self.word_list.update(word_list)

        return word_list

    @staticmethod
    def get_tag_text(tag, tag_name, attr):
        """ """
        return ''.join([x.get_text() for x in tag.find_all(tag_name, attr)])

    @staticmethod
    def get_tag_attr(tag, tag_name, attr, base_url, attr_name):
        """ """
        return ''.join([urljoin(base_url, x[attr_name]) for x in tag.find_all(tag_name, attr) if x.has_attr(attr_name)])

    def parse_example_list(self, soup):
        """ """
        result = []
        for div in soup.select('#tmTable > div'):
            buf = {}
            for ltr in div.find_all('div', {'dir': 'ltr'}):
                lang = ltr['lang']

                text = self.get_tag_text(tag=ltr, tag_name='span', attr={'class': ['tm-p-', 'tm-p-em']})
                author = self.get_tag_text(tag=ltr, tag_name='span', attr={'title': 'author'})
                author_url = self.get_tag_attr(
                    tag=ltr,
                    tag_name='div',
                    attr={'class': 'user-avatar-box'},
                    base_url=self.base_url,
                    attr_name='authorurl'
                )

                item = {
                    lang + '_text': text,
                    lang + '_author': author,
                    lang + '_author_url': author_url,
                }
                buf.update(item)

            result.append(buf)

        return result

    def parse_article(self, soup):
        """ """
        result = soup.find_all('article')
        if result is not None:
            try:
                result = result[0]
                if result.get_text().strip() == '':
                    result = None
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '본문 없음',
                    'exception': str(e),
                    'article': str(result),
                    'soup': str(soup),
                })

                result = None

        return result

    def get_example(self, page, url):
        """ """
        url = '{url}?page={page}&tmmode=MUST'.format(page=page, url=url)
        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '예문 조회',
            'page': page,
            'url': url,
        })

        try:
            resp = self.session.get(url, timeout=120)
        except ConnectionError:
            return {'error': 'connection'}

        soup = BeautifulSoup(resp.content, 'html5lib')

        # login_btn = soup.select('#topCollapseNavContainer > ul > li > a')
        # print({'login_btn', str(login_btn)})

        word_list = self.parse_word_list(soup=soup)
        example_list = self.parse_example_list(soup=soup)
        article = self.parse_article(soup=soup)

        if article is None:
            return {'error': 'empty article'}

        next_btn = soup.select_one('#translationExamples div.pagination a')

        next_url = ''
        if len(example_list) > 0 and next_btn is not None:
            next_url = urljoin(self.base_url, next_btn['href'])

        return {
            'article': article,
            'examples': example_list,
            'next_url': next_url,
            'word_list': word_list,
        }

    def trace_example_list(self, entry, url, page=1):
        """ """
        max_try = 5
        resp = {'next_url': 'start'}

        while resp['next_url'] != '':
            resp = self.get_example(page=page, url=url)
            if 'error' in resp:
                if resp['error'] == 'connection':
                    max_try -= 1
                    if max_try < 0:
                        break

                    resp = {'next_url': 'retry'}
                    sleep(100)
                    continue
                else:
                    return resp

            page += 1
            max_try = 5

            dt = datetime.now(tz=self.timezone).isoformat()

            # save resp
            for doc in resp['examples']:
                doc['_id'] = str(uuid4())
                doc['date'] = dt

                self.elastic.save_document(document=doc, delete=False, index=self.env.example)

            self.elastic.flush()

            for w_url in resp['word_list']:
                if w_url in self.history:
                    continue

                doc_word = resp['word_list'][w_url]

                doc = {
                    '_id': doc_word['document_id'],
                    'url': w_url,
                    'date': dt,
                    'entry': doc_word['entry'],
                }
                self.elastic.save_document(document=doc, delete=False, index=self.env.word_list)

            self.elastic.flush()

            if resp['article'] is not None:
                doc = {
                    '_id': str(uuid4()),
                    'date': dt,
                    'entry': entry,
                    'article': str(resp['article']),
                }

                self.elastic.save_document(document=doc, delete=False, index=self.env.article)
                self.elastic.flush()

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '예문 조회',
                'entry': entry,
                'page': page,
                'example size': len(resp['examples']),
                'word_list size': len(resp['word_list']),
                'next_url': resp['next_url'],
            })

            sleep(self.env.sleep)

        return {'status': 'ok'}

    def save_as_done(self, document_id):
        """ """
        doc = {
            '_id': document_id,
            'state': 'done',
        }
        self.elastic.save_document(document=doc, delete=False, index=self.env.word_list)
        self.elastic.flush()
        return

    def get_word_list(self):
        """ """
        doc_list = self.elastic.dump(index=self.env.word_list)

        for doc in doc_list:
            if 'state' in doc and doc['state'] == 'done':
                self.history.add(doc['url'])
                continue

            self.word_list[doc['url']] = {
                'entry': doc['entry'],
                'document_id': doc['document_id'],
            }

        return

    def trace_word_list(self):
        """ """
        count = 0

        url_list = list(self.word_list.keys())
        for url in url_list:
            if url in self.history:
                continue

            count += 1

            word_info = self.word_list[url]

            resp = self.trace_example_list(entry=word_info['entry'], url=url)
            if 'error' in resp:
                break

            self.history.add(url)
            self.save_as_done(document_id=word_info['document_id'])

            sleep(self.env.sleep)

        if count > 0:
            self.trace_word_list()

        return

    def batch(self):
        """"""

        self.env = self.init_arguments()

        self.login_info['username'] = self.env.username
        self.login_info['password'] = self.env.password

        self.open_db(index=self.env.example)

        self.get_word_list()

        self.login()
        sleep(10)

        self.trace_word_list()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--host', default='https://corpus.ncsoft.com:9200', help='')
        parser.add_argument('--auth', default='crawler:crawler2019', help='')

        parser.add_argument('--username', default='ejpark78@gmail.com', help='')
        parser.add_argument('--password', default='nlplab', help='')

        parser.add_argument('--example', default='crawler-dictionary-example-glosbe-koen', help='')
        parser.add_argument('--article', default='crawler-dictionary-example-glosbe-koen-article', help='')
        parser.add_argument('--word_list', default='crawler-dictionary-example-glosbe-koen-word-list', help='')

        parser.add_argument('--sleep', default=60, type=int, help='')

        return parser.parse_args()


if __name__ == '__main__':
    GlosbeCrawler().batch()
