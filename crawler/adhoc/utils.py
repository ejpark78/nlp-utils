#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ssl
from base64 import decodebytes
from collections import defaultdict
from datetime import datetime, timedelta
from logging import LoggerAdapter, WARNING, INFO, DEBUG
from os import getenv
from ssl import SSLContext
from urllib.parse import urlparse, parse_qs

import pytz
import urllib3
from berkeleydb import hashopen
from dateutil.parser import parse as parse_date
from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context
from scrapy.utils.project import data_path
from scrapy.settings import Settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


class AdhocUtils(object):

    def __init__(self, allowed_domains: list, index: str, allowed_url_query: str, history_lifetime: int,
                 logger: LoggerAdapter, settings: Settings):
        self.index = index
        self.logger = logger
        self.settings = settings

        self.allowed_domains = allowed_domains

        self.allowed_urls = {
            'query': set(allowed_url_query.split(','))
        }

        self.host = getenv('ELASTIC_SEARCH_HOST', default='https://corpus.ncsoft.com:9200')
        self.http_auth = getenv('ELASTIC_SEARCH_AUTH', default=None)
        self.http_auth_enc = getenv('ELASTIC_SEARCH_AUTH_ENCODED', default='ZWxhc3RpYzpubHBsYWI=')

        self.es = None
        self.tz = pytz.timezone('Asia/Seoul')

        self.history = set()
        self.history_db = None
        self.history_lifetime = timedelta(hours=history_lifetime)

        self.mapping = {
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

        self.summary = defaultdict(int)

        self.cache_dir = data_path('', createdir=True).rstrip('/')

    @staticmethod
    def get_doc_id(url: str) -> str:
        parsed_url = urlparse(url)

        path = parsed_url.path.strip('/').replace('/', '-')

        q = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}
        if len(q) == 0:
            return path

        q_str = '-'.join([f"{k}-{q[k]}" for k in sorted(q.keys())])
        return f'{path}-{q_str}'

    def del_old_history(self) -> None:
        limit = datetime.now(tz=self.tz) - self.history_lifetime

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

            count = len(urls) - len(self.history_db)
            self.summary['history deleted count'] += count

            self.logger.log(level=DEBUG, msg=f'old history deleted ({limit}): {count}')

        return None

    def is_skip(self, url: str) -> bool:
        # check query: excludes['query'] = set('page')
        url_query = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
        for q, _ in url_query.items():
            if q in self.allowed_urls['query']:
                self.summary['page url'] += 1
                return False

        # check history
        if url.encode('utf-8') in self.history_db or url in self.history:
            self.summary['skip in history'] += 1
            self.logger.log(level=DEBUG, msg=f'skip in history: {url}')
            return True

        # check domains
        for domain in self.allowed_domains:
            if domain in url:
                self.history.add(url)
                self.summary['history count'] = len(self.history)
                return False

        self.summary['out of allowed domains'] += 1
        self.logger.log(level=DEBUG, msg=f'skip url (out of allowed domains): {url}')
        return True

    def save_document(self, doc: dict, doc_id: str) -> None:
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
            _ = self.es.bulk(index=self.index, body=bulk, refresh=True)

            self.summary['saved doc count'] += 1

            self.history_db[doc['url'].encode('utf-8')] = datetime.now(tz=self.tz).isoformat().encode('utf-8')
            self.history_db.sync()

            self.summary['history_db count'] = len(self.history_db)
        except Exception as e:
            self.logger.log(level=WARNING, msg=str(e))

        return None

    @staticmethod
    def get_ssl_verify_mode() -> SSLContext:
        ssl_context = create_ssl_context()

        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        return ssl_context

    def create_index(self, es: Elasticsearch, index: str) -> bool:
        """인덱스를 생성한다."""
        if es is None or es.indices.exists(index=index) is True:
            return False

        try:
            es.indices.create(index=index, body=self.mapping)
        except Exception as e:
            self.logger.log(level=WARNING, msg=str(e))
            return False

        return True

    def open(self) -> None:
        self.history_db = hashopen(f"{self.cache_dir}/{self.settings['URL_HISTORY_FILENAME']}", 'w')

        if self.es is not None:
            return

        if self.http_auth is None:
            self.http_auth = decodebytes(self.http_auth_enc.encode('utf-8')).decode('utf-8')

        self.es = Elasticsearch(
            hosts=self.host,
            http_auth=self.http_auth,
            verify_certs=False,
            ssl_show_warn=False,
            ssl_context=self.get_ssl_verify_mode(),
            http_compress=True,
        )

        return None
