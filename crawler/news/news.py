#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from argparse import Namespace
from time import sleep

import requests
import urllib3
import yaml
import pytz
from datetime import datetime
from dateutil.parser import parse as parse_date

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class NewsCrawler(object):
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
        self.logger.log(msg=url_info)

        elastic = ElasticSearchUtils(
            host=job['host'],
            index=None,
            bulk_size=20,
            http_auth=job['http_auth'],
        )

        resp = requests.get(url=url_info['url_frame'])

        doc = resp.json()
        for card in doc['cards']:
            for item in card['contents']:
                item['_id'] = item['etag']

                index = job['index_list'].format(year=parse_date(item['updated']).year)
                elastic.save_document(document=item, index=index)

                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '슬립',
                    'index': index,
                    'sleep': self.params.sleep,
                })
                sleep(self.params.sleep)

                self.get_article(job=job, list_info=item, elastic=elastic)

                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '슬립',
                    'sleep': self.params.sleep,
                })
                sleep(self.params.sleep)

        return

    def get_article(self, job: dict, list_info: dict, elastic: ElasticSearchUtils) -> None:
        resp = requests.get(url=list_info['gcsUrl'])
        doc = resp.json()

        doc['_id'] = doc['etag']

        index = job['index'].format(year=parse_date(list_info['updated']).year)
        elastic.save_document(document=doc, index=index)

        flag = elastic.flush()

        # 성공 로그 표시
        if flag is True:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '기사 저장 성공',
                'doc_url': '{host}/{index}/_doc/{id}?pretty'.format(
                    id=doc['document_id'],
                    host=elastic.host,
                    index=index,
                ),
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

        return parser.parse_args()


if __name__ == '__main__':
    NewsCrawler().batch()
