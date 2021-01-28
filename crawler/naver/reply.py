#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
import re
from copy import deepcopy
from datetime import datetime
from time import sleep
from urllib.parse import urljoin
from urllib.parse import urlparse, parse_qs

import pytz
import requests
import urllib3
import yaml
from cachelib import SimpleCache
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class NaverNewsReplyCrawler(object):
    """네이버 뉴스 댓글 수집기"""

    def __init__(self):
        super().__init__()

        self.env = None

        self.timezone = pytz.timezone('Asia/Seoul')

        self.stop_columns = [
            'idType', 'lang', 'country', 'idProvider', 'visible', 'containText',
            'maskedUserName', 'commentType', 'expose', 'profileType', 'regTimeGmt',
            'modTimeGmt', 'templateId', 'userProfileImage',
        ]

        self.sleep_time = 10

        self.headers = {
            'mobile': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                              'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                              'Version/11.0 Mobile/15A372 Safari/604.1'
            },
            'desktop': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/87.0.4280.141 Safari/537.36'
            }
        }

        self.cache = SimpleCache()

        self.logger = Logger()

    def set_history(self, value: set, name: str) -> None:
        """문서 아이디 이력을 저장한다."""
        self.cache.set(name, value, timeout=600)
        return

    def get_history(self, name: str, default: set) -> set:
        """문서 아이디 이력을 반환한다."""
        value = self.cache.get(name)

        if value is None:
            value = default
            self.cache.set(name, value, timeout=600)

        return value

    def trace_elasticsearch(self, url_frame: dict, date: datetime, elastic: dict) -> None:
        """특정 날짜의 뉴스 목록을 따라간다."""
        query_cond = {
            'query': {
                'bool': {
                    'must': [{
                        'range': {
                            'date': {
                                'format': 'yyyy-MM-dd',
                                'gte': date.strftime('%Y-%m-%d'),
                                'lte': date.strftime('%Y-%m-%d')
                            }
                        }
                    }]
                }
            }
        }

        id_list = elastic['news'].get_id_list(
            size=1000,
            index=elastic['news'].index,
            query_cond=query_cond,
        )

        # url 저장 이력 조회
        doc_history = self.get_history(name='doc_history', default=set())

        for doc_id in id_list:
            # 중복 확인
            if self.is_dup_reply(
                    news={'url': ''},
                    index=elastic['reply'].index,
                    doc_id=doc_id,
                    url_frame=url_frame,
                    doc_history=doc_history,
                    elastic_utils=elastic['reply'],
            ) is True:
                continue

            # 원본 기사를 가져온다.
            doc = self.get_news(elastic=elastic['news'], doc_id=doc_id)
            if len(doc) == 0:
                continue

            url_info = self.get_query(doc['url'])
            doc.update(url_info)

            news = self.get_reply(news=doc, url_frame=url_frame)

            # 문서 저장
            self.save_reply(
                news=news,
                date=date,
                doc_id=doc_id,
                elastic_utils=elastic['reply'],
            )

        return

    def is_dup_reply(self, url_frame: dict, news: dict, elastic_utils: ElasticSearchUtils, index: str, doc_id: str,
                     doc_history) -> bool:
        """특정 날짜의 뉴스 목록을 따라간다."""
        if self.env.overwrite is True:
            return False

        if 'check_id' in url_frame and url_frame['check_id'] is False:
            return False

        reply_info = None
        for k in ['totalCount', 'reply_count']:
            if k not in news:
                continue

            reply_info = {
                'count': news['totalCount'],
                'source': 'totalCount',
            }
            break

        is_skip = self.check_doc_id(
            url=news['url'],
            index=index,
            doc_id=doc_id,
            doc_history=doc_history,
            reply_info=reply_info,
            elastic_utils=elastic_utils,
        )

        if is_skip is True:
            return True

        return False

    def check_doc_id(self, doc_id: str, elastic_utils: ElasticSearchUtils, url: str, index: str, doc_history: set,
                     reply_info: dict = None) -> bool:
        """문서 아이디를 이전 기록과 비교한다."""
        # 캐쉬에 저장된 문서가 있는지 조회
        if doc_id in doc_history:
            self.logger.info(msg={
                'level': 'INFO',
                'message': '중복 문서, 건너뜀',
                'doc_id': doc_id,
                'url': url,
            })
            return True

        # 문서가 있는지 조회
        is_exists = elastic_utils.conn.exists(index=index, id=doc_id)
        if is_exists is False:
            return False

        # 댓글 정보 추가 확인
        if reply_info is not None:
            field_name = reply_info['source']
            doc = elastic_utils.conn.get(
                id=doc_id,
                index=index,
                _source=[field_name],
            )['_source']

            if field_name not in doc:
                return False

            if doc[field_name] != reply_info['count']:
                return False

        doc_history.add(doc_id)

        self.logger.info(msg={
            'level': 'INFO',
            'message': 'elasticsearch 에 존재함, 건너뜀',
            'doc_id': doc_id,
            'url': url,
        })

        return True

    @staticmethod
    def open_elasticsearch(date: datetime, job: dict, url_frame: dict) -> dict:
        """elasticsearch 연결"""
        index_tag = None
        if date is not None:
            index_tag = date.year

        elastic_reply = ElasticSearchUtils(
            tag=index_tag,
            host=job['host'],
            index=job['index'],
            bulk_size=20,
            http_auth=job['http_auth'],
        )

        elastic_news_list = ElasticSearchUtils(
            tag=index_tag,
            host=job['host'],
            index=url_frame['list_index'],
            bulk_size=20,
            http_auth=job['http_auth'],
        )

        return {
            'reply': elastic_reply,
            'news': elastic_news_list
        }

    def get_news(self, elastic: ElasticSearchUtils, doc_id: str) -> dict:
        """원문 기사를 가져온다."""
        try:
            return elastic.conn.get(
                id=doc_id,
                index=elastic.index,
                _source=['url', 'title', 'date'],
            )['_source']
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '원문 기사 조회 에러',
                'exception': str(e),
            })

        return {}

    def trace_reply_list(self, url_frame: dict, date: datetime, elastic: dict) -> None:
        """특정 날짜의 뉴스 목록을 따라간다."""
        # url 저장 이력 조회
        doc_history = self.get_history(name='doc_history', default=set())

        headers = deepcopy(self.headers['desktop'])

        query = {
            'date': date.strftime(url_frame['date_format']),
            'page': 1,
            'total': 500,
        }

        while query['page'] <= query['total']:
            url = url_frame['list'].format(**query)

            headers['Referer'] = url_frame['Referer'].format(**query)
            news_info = requests.get(url=url, headers=headers, verify=False).json()

            query['total'] = news_info['totalPages']

            for news in news_info['list']:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '기사 정보',
                    'news': news,
                    'query': query,
                })

                if 'url' not in news or news['url'] is None:
                    self.logger.error(msg={
                        'level': 'ERROR',
                        'message': 'empty url',
                        'news': news,
                    })
                    continue

                # 예외 처리
                if news['url'][:2] == '//':
                    news['url'] = '/kbo/' + news['url'][2:]

                news['url'] = urljoin(url_frame['list'], news['url'])

                doc_id = '{oid}-{aid}'.format(**news)

                # 중복 확인
                if self.is_dup_reply(
                        news=news,
                        index=elastic['reply'].index,
                        doc_id=doc_id,
                        url_frame=url_frame,
                        doc_history=doc_history,
                        elastic_utils=elastic['reply'],
                ) is True:
                    continue

                # 원본 기사를 가져온다.
                doc = self.get_news(elastic=elastic['news'], doc_id=doc_id)
                if len(doc) > 0:
                    news.update(doc)

                # 댓글 조회
                news = self.get_reply(news=news, url_frame=url_frame)

                # 문서 저장
                self.save_reply(
                    news=news,
                    date=date,
                    doc_id=doc_id,
                    elastic_utils=elastic['reply'],
                )

                sleep(self.sleep_time)

            query['page'] += 1

        return

    def save_reply(self, elastic_utils: ElasticSearchUtils, news: dict, doc_id: str, date: datetime) -> None:
        news['_id'] = doc_id
        news['date'] = date

        elastic_utils.save_document(document=news)
        elastic_utils.flush()

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '문서 저장 성공',
            'doc_url': elastic_utils.get_doc_url(document_id=doc_id),
        })

        return

    def get_reply(self, news: dict, url_frame: dict) -> dict:
        """댓글을 가져온다."""
        result = []

        query = {
            'oid': news['oid'],
            'aid': news['aid'],
            'page': 1,
            'total': 500,
        }

        while query['page'] <= query['total']:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '댓글 조회',
                'news': news,
                'query': query,
            })

            reply_list, query['total'] = self.extract_reply_list(
                query=query,
                base_url=news['url'],
                url_frame=url_frame,
            )
            result += reply_list

            sleep(self.sleep_time)

        news['reply_list'] = result
        news['reply_count'] = len(result)

        return news

    def extract_reply_list(self, base_url: str, query: dict, url_frame: dict) -> (list, int):
        """댓글 목록을 추출해서 반환한다."""
        headers = deepcopy(self.headers['desktop'])

        headers['Referer'] = base_url

        url = ''
        try:
            url = url_frame['reply'].format(**query)
            resp = requests.get(url=url, headers=headers, verify=False)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '댓글 조회 에러',
                'url': url,
                'query': query,
                'url_frame': url_frame,
                'exception': str(e),
            })

            return [], 0

        query['page'] += 1

        callback = {}
        try:
            callback = re.sub(r'_callback\((.+)\);$', r'\g<1>', resp.text)
            callback = json.loads(callback)

            comment_list = callback['result']['commentList']
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '댓글 파싱 에러',
                'callback': callback,
                'exception': str(e),
            })

            return [], 0

        result = []
        for item in comment_list:
            new_value = {}
            for k in item:
                if k in self.stop_columns:
                    continue

                if item[k] is None or item[k] is False or item[k] == '':
                    continue

                new_value[k] = item[k]

            result.append(new_value)

        return result, callback['result']['pageModel']['totalPages']

    @staticmethod
    def get_query(url: str) -> dict:
        """ url 에서 쿼리문을 반환 """
        url_info = urlparse(url)
        result = parse_qs(url_info.query)
        for key in result:
            result[key] = result[key][0]

        return result

    @staticmethod
    def open_config(filename: str) -> dict:
        with open(filename, 'r') as fp:
            return dict(yaml.load(stream=fp, Loader=yaml.FullLoader))

    def batch(self) -> None:
        """날짜 범위에 있는 댓글을 수집한다."""
        self.env = self.init_arguments()

        config = self.open_config(filename=self.env.config)

        step = -1

        # 날짜 범위 추출
        if self.env.date_range is None:
            today = datetime.now(self.timezone)

            start_date = today + relativedelta(weeks=-1)
            end_date = today
        else:
            start_date, end_date = self.env.date_range.split('~')

            start_date = parse_date(start_date)
            start_date = self.timezone.localize(start_date)

            end_date = parse_date(end_date)
            end_date = self.timezone.localize(end_date)

        date_list = list(rrule(DAILY, dtstart=start_date, until=end_date))
        if step < 0:
            date_list = sorted(date_list, reverse=True)

        # 날짜별 크롤링 시작
        for dt in date_list:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '날짜',
                'date': str(dt)
            })

            for job in config['jobs']:
                # override elasticsearch config
                job['host'] = os.getenv(
                    'ELASTIC_SEARCH_HOST',
                    default=job['host'] if 'host' in job else None
                )
                job['index'] = os.getenv(
                    'ELASTIC_SEARCH_INDEX',
                    default=job['index'] if 'index' in job else None
                )
                job['http_auth'] = os.getenv(
                    'ELASTIC_SEARCH_AUTH',
                    default=job['http_auth'] if 'http_auth' in job else None
                )

                for url_frame in job['list']:
                    elastic = self.open_elasticsearch(date=dt, job=job, url_frame=url_frame)

                    if url_frame['list'] == 'elasticsearch':
                        self.trace_elasticsearch(url_frame=url_frame, date=dt, elastic=elastic)
                    else:
                        self.trace_reply_list(url_frame=url_frame, date=dt, elastic=elastic)

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--overwrite', action='store_true', default=False, help='덮어쓰기')

        parser.add_argument('--date-range', default=None, help='date 날짜 범위: 2000-01-01~2019-04-10')

        parser.add_argument('--sleep', default=10, type=int, help='sleep time')

        parser.add_argument('--config', default=None, help='설정 파일 정보')

        return parser.parse_args()


if __name__ == '__main__':
    NaverNewsReplyCrawler().batch()
