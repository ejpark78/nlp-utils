#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
from argparse import Namespace
from datetime import datetime
from time import sleep

import pytz
import requests
import urllib3
import yaml
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from crawler.utils.elasticsearch import ElasticSearchUtils
from crawler.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class ApNewsCrawler(object):
    """뉴스 크롤러"""

    def __init__(self):
        super().__init__()

        self.config = None
        self.params = None

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

    @staticmethod
    def open_config(filename: str) -> dict:
        with open(filename, 'r') as fp:
            return dict(yaml.load(stream=fp, Loader=yaml.FullLoader))

    def trace_list(self, job: dict, url_info: dict) -> None:
        job['host'] = os.getenv('ELASTIC_SEARCH_HOST', default=job['host'] if 'host' in job else None)

        job['index'] = os.getenv('ELASTIC_SEARCH_INDEX', default=job['index'] if 'index' in job else None)

        job['http_auth'] = os.getenv(
            'ELASTIC_SEARCH_AUTH',
            default=job['http_auth'] if 'http_auth' in job else None
        )

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': 'trace_list',
            **url_info
        })

        elastic = ElasticSearchUtils(
            host=job['host'],
            index=None,
            bulk_size=20,
            http_auth=job['http_auth'],
            mapping=self.params.mapping
        )

        resp = requests.get(url=url_info['url_frame'])

        try:
            card_list = resp.json()['cards']
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'resp json 파싱 에러 ',
                'resp': resp.text,
                'exception': str(e),
            })
            return

        for card in card_list:
            for item in card['contents']:
                dt = parse_date(item['updated'])
                html = BeautifulSoup(item['storyHTML']).find('html')

                doc = {
                    '_id': item['etag'],
                    'title': item['headline'],
                    'content': html.get_text() if html is not None else '',
                    'date': dt.isoformat(),
                    'raw': json.dumps(item, ensure_ascii=False),
                    '@curl_date': datetime.now(self.timezone).isoformat()
                }

                index = job['index_list'].format(year=dt.year)
                elastic.save_document(document=doc, index=index, delete=True)

                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '슬립',
                    'index': index,
                    'sleep': self.params.sleep,
                })
                sleep(self.params.sleep)

                self.get_article(job=job, url=item['gcsUrl'], date=dt, elastic=elastic)

                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '슬립',
                    'sleep': self.params.sleep,
                })
                sleep(self.params.sleep)

        return

    def get_article(self, job: dict, url: str, date: datetime, elastic: ElasticSearchUtils) -> None:
        resp = requests.get(url=url).json()
        html = BeautifulSoup(resp['storyHTML']).find('html')

        doc = {
            '_id': resp['etag'],
            'title': resp['headline'],
            'content': html.get_text() if html is not None else '',
            'date': date.isoformat(),
            'raw': json.dumps(resp, ensure_ascii=False),
            '@curl_date': datetime.now(self.timezone).isoformat()
        }

        doc_id = doc['_id']

        index = job['index'].format(year=date.year)
        elastic.save_document(document=doc, index=index, delete=True)

        # 성공 로그 표시
        if elastic.flush() is True:
            elastic.index = index

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '기사 저장 성공',
                'doc_url': elastic.get_doc_url(document_id=doc_id),
                **{k: doc[k] for k in ['updated', 'headline'] if k in doc},
            })

        return

    def batch(self) -> None:
        self.params = self.init_arguments()

        self.config = self.open_config(filename=self.params.config)

        for job in self.config['jobs']:
            for item in job['list']:
                dt = datetime.now(tz=self.timezone)
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '뉴스 목록 크롤링',
                    'date': dt.strftime('%Y-%m-%d') if dt is not None else '',
                    **item
                })

                self.trace_list(job=job, url_info=item)

        return

    @staticmethod
    def init_arguments() -> Namespace:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--sleep', default=10, type=float, help='sleep time')
        parser.add_argument('--config', default=None, type=str, help='설정 파일 정보')
        parser.add_argument('--mapping', default=None, type=str, help='인덱스 맵핑 파일 정보')

        return parser.parse_args()


if __name__ == '__main__':
    ApNewsCrawler().batch()
