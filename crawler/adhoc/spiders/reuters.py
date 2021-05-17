#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ssl
from base64 import decodebytes
from datetime import datetime, timedelta
from logging import WARNING, INFO
from os import getenv
from ssl import SSLContext
from urllib.parse import urlparse, parse_qs
from dateutil.parser import parse as parse_date

import pytz
import scrapy
import urllib3
from berkeleydb import hashopen
from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context
from scrapy.http.response.html import HtmlResponse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


class ReutersSpider(scrapy.Spider):
    name = 'reuters'
    allowed_domains = ['www.reuters.com']

    start_urls = [
        'https://www.reuters.com/'
    ]

    index = 'adhoc-reuters'

    deep = max_deep = 1024

    max_history = timedelta(days=1)

    host = getenv('ELASTIC_SEARCH_HOST', default='https://corpus.ncsoft.com:9200')
    http_auth = getenv('ELASTIC_SEARCH_AUTH_ENCODED', default='ZWxhc3RpYzpubHBsYWI=')

    es, tz = None, pytz.timezone('Asia/Seoul')

    history, history_db = set(), None

    def start_requests(self):
        self.history_db = hashopen('url_history.db', 'w')

        self.del_old_history()

        if self.es is None:
            self.es = Elasticsearch(
                hosts=self.host,
                http_auth=decodebytes(self.http_auth.encode('utf-8')).decode('utf-8'),
                verify_certs=False,
                ssl_show_warn=False,
                ssl_context=self.get_ssl_verify_mode(),
                http_compress=True,
            )

        for url in self.start_urls:
            self.deep = self.max_deep

            yield scrapy.Request(url, callback=self.extract_url, cb_kwargs=dict(is_start=True))

    def extract_url(self, response: HtmlResponse, is_start: bool = False):
        self.deep -= 1
        if self.deep < 0:
            return

        doc_id = self.get_doc_id(url=response.url)
        self.save_document(doc_id=doc_id, doc={
            'url': response.url,
            'raw': response.body.decode('utf-8')
        })

        for link_tag in response.css('body a'):
            url = link_tag.css('::attr(href)').get()
            if url is None or url == '' or url[0] == '#' or url in {'//'}:
                continue

            if is_start is False and self.is_skip(url=response.urljoin(url)):
                continue

            self.logger.log(level=INFO, msg=url)

            yield response.follow(url, callback=self.extract_url)

    @staticmethod
    def get_doc_id(url: str) -> str:
        parsed_url = urlparse(url)

        path = parsed_url.path.strip('/').replace('/', '-')

        q = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}
        if len(q) == 0:
            return path

        q_str = '-'.join([f"{k}-{q[k]}" for k in sorted(q.keys())])
        return f'{path}-{q_str}'

    def del_old_history(self):
        limit = datetime.now(tz=self.tz) - self.max_history

        urls = list(self.history_db.keys())
        sync = False
        for k in urls:
            dt = parse_date(self.history_db[k].decode('utf-8')).astimezone(self.tz)
            if dt < limit:
                continue

            sync = True
            del self.history_db[k]

        if sync:
            self.history_db.sync()

    def is_skip(self, url: str) -> bool:
        if url.encode('utf-8') in self.history_db or url in self.history:
            self.logger.log(level=INFO, msg=f'skip url (in history): {url}')
            return True

        for domain in self.allowed_domains:
            if domain in url:
                self.history.add(url)
                return False

        self.logger.log(level=INFO, msg=f'skip url (out of allowed domains): {url}')
        return True

    def save_document(self, doc: dict, doc_id: str):
        if doc_id == '' or doc_id is None:
            self.logger.log(level=INFO, msg=f"missing doc_id: {doc_id}")
            return

        self.create_index(es=self.es, index=self.index)

        doc['@crawl_date'] = datetime.now(tz=self.tz).isoformat()

        bulk = [{
            'update': {
                '_id': doc_id,
                '_index': self.index,
            }
        }, {
            'doc': doc,
            'doc_as_upsert': True,
        }]

        try:
            resp = self.es.bulk(index=self.index, body=bulk, refresh=True)

            self.history_db[doc['url'].encode('utf-8')] = datetime.now(tz=self.tz).isoformat().encode('utf-8')
            self.history_db.sync()
        except Exception as e:
            self.logger.log(level=WARNING, msg=str(e))

    @staticmethod
    def get_ssl_verify_mode() -> SSLContext:
        ssl_context = create_ssl_context()

        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        return ssl_context

    @staticmethod
    def create_index(es: Elasticsearch, index: str) -> bool:
        """인덱스를 생성한다."""
        if es is None or es.indices.exists(index=index) is True:
            return False

        mapping = {
            'settings': {
                'number_of_shards': 1,
                'number_of_replicas': 1
            },
            'mappings': {
                'properties': {
                    'url': {
                        'type': 'keyword'
                    },
                    'raw': {
                        'enabled': False
                    },
                    '@crawl_date': {
                        'type': 'date'
                    }
                }
            }
        }

        try:
            es.indices.create(index=index, body=mapping)
        except Exception as e:
            return False

        return True

"""

# url 복원 
'https://www.reuters.com/video/watch/biden-says-gop-is-having-mini-revolution-id729582174?chan=6g5ka85'
'https://www.reuters.com/news/archive/instagram.com/instagram.com//instagram.com/reuters?view=page&page=2&pageSize=10'
'https://www.reuters.com/news/archive/France-news?view=page&page=7&pageSize=10'

"""
