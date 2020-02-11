#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import re
import sys
from copy import deepcopy
from datetime import datetime
from time import sleep
from urllib.parse import urljoin

import requests
import urllib3
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY

from module.crawler_base import CrawlerBase
from module.utils.elasticsearch_utils import ElasticSearchUtils
from module.utils.logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MESSAGE = 25

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(format='%(message)s')

logger = logging.getLogger()

logger.setLevel(MESSAGE)
logger.handlers = [logging.StreamHandler(sys.stderr)]


class NaverNewsReplyCrawler(CrawlerBase):
    """네이버 뉴스 댓글 수집기"""

    def __init__(self, category='', job_id='', column='', config=None):
        """ 생성자 """
        super().__init__()

        self.config = config

        self.job_category = category
        self.job_id = job_id
        self.column = column

        self.stop_columns = [
            'idType', 'lang', 'country', 'idProvider', 'visible', 'containText',
            'maskedUserName', 'commentType', 'expose', 'profileType', 'regTimeGmt',
            'modTimeGmt', 'templateId', 'userProfileImage',
        ]

    def batch(self, date_range, step=-1):
        """날짜 범위에 있는 댓글을 수집한다."""
        self.update_config()

        # 날짜 범위 추출
        if date_range is None:
            today = datetime.now(self.timezone)

            start_date = today + relativedelta(weeks=-1)
            end_date = today
        else:
            start_date, end_date = date_range.split('~')

            start_date = parse_date(start_date)
            start_date = self.timezone.localize(start_date)

            end_date = parse_date(end_date)
            end_date = self.timezone.localize(end_date)

        date_list = list(rrule(DAILY, dtstart=start_date, until=end_date))
        if step < 0:
            date_list = sorted(date_list, reverse=True)

        # 날짜별 크롤링 시작
        for dt in date_list:
            msg = {
                'level': 'ERROR',
                'message': '날짜',
                'date': str(dt)
            }
            logger.error(msg=LogMsg(msg))

            for job in self.job_info:
                if 'split_index' not in job:
                    job['split_index'] = False

                self.sleep_time = job['sleep']

                for url_frame in job['list']:
                    elastic = self.open_elasticsearch(date=dt, job=job, url_frame=url_frame)

                    if url_frame['list'] == 'elasticsearch':
                        self.trace_elasticsearch(url_frame=url_frame, date=dt, elastic=elastic)
                    else:
                        self.trace_reply_list(url_frame=url_frame, date=dt, elastic=elastic)

        return

    def trace_elasticsearch(self, url_frame, date, elastic):
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
        doc_history = self.get_history(name='doc_history', default={})

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

    def is_dup_reply(self, url_frame, news, elastic_utils, index, doc_id, doc_history):
        """특정 날짜의 뉴스 목록을 따라간다."""
        if self.cfg.debug == 1:
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

    @staticmethod
    def open_elasticsearch(date, job, url_frame):
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
            split_index=job['split_index'],
        )

        elastic_news_list = ElasticSearchUtils(
            tag=index_tag,
            host=job['host'],
            index=url_frame['list_index'],
            bulk_size=20,
            http_auth=job['http_auth'],
            split_index=job['split_index'],
        )

        return {
            'reply': elastic_reply,
            'news': elastic_news_list
        }

    @staticmethod
    def get_news(elastic, doc_id):
        """원문 기사를 가져온다."""
        try:
            return elastic.elastic.get(
                id=doc_id,
                index=elastic.index,
                _source=['url', 'title', 'date'],
                doc_type='_doc',
            )['_source']
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '원문 기사 조회 에러',
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        return {}

    def trace_reply_list(self, url_frame, date, elastic):
        """특정 날짜의 뉴스 목록을 따라간다."""
        # url 저장 이력 조회
        doc_history = self.get_history(name='doc_history', default={})

        headers = deepcopy(self.headers['desktop'])

        query = {
            'date': date.strftime(url_frame['date_format']),
            'page': 1,
            'total': 500,
        }

        while query['page'] <= query['total']:
            url = url_frame['list'].format(**query)

            headers['Referer'] = url_frame['Referer'].format(**query)
            news_info = requests.get(url=url, headers=headers).json()

            query['total'] = news_info['totalPages']

            for news in news_info['list']:
                msg = {
                    'level': 'MESSAGE',
                    'message': '기사 정보',
                    'news': news,
                    'query': query,
                }
                logger.log(level=MESSAGE, msg=LogMsg(msg))

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

    @staticmethod
    def save_reply(elastic_utils, news, doc_id, date):
        """ """
        news['_id'] = doc_id
        news['date'] = date

        elastic_utils.save_document(document=news)
        elastic_utils.flush()

        msg = {
            'level': 'MESSAGE',
            'message': '문서 저장 성공',
            'doc_url': '{host}/{index}/_doc/{id}?pretty'.format(
                host=elastic_utils.host,
                index=elastic_utils.index,
                id=doc_id,
            ),
        }
        logger.log(level=MESSAGE, msg=LogMsg(msg))

        return

    def get_reply(self, news, url_frame):
        """댓글을 가져온다."""
        result = []

        query = {
            'oid': news['oid'],
            'aid': news['aid'],
            'page': 1,
            'total': 500,
        }

        while query['page'] <= query['total']:
            msg = {
                'level': 'MESSAGE',
                'message': '댓글 조회',
                'news': news,
                'query': query,
            }
            logger.log(level=MESSAGE, msg=LogMsg(msg))

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

    def extract_reply_list(self, base_url, query, url_frame):
        """댓글 목록을 추출해서 반환한다."""
        headers = deepcopy(self.headers['desktop'])

        headers['Referer'] = base_url

        try:
            url = url_frame['reply'].format(**query)
            resp = requests.get(url=url, headers=headers)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '댓글 조회 에러',
                'url': url,
                'query': query,
                'url_frame': url_frame,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

            return [], 0

        query['page'] += 1

        callback = {}
        try:
            callback = re.sub(r'_callback\((.+)\);$', r'\g<1>', resp.text)
            callback = json.loads(callback)

            comment_list = callback['result']['commentList']
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '댓글 파싱 에러',
                'callback': callback,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

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
    def get_query(url):
        """ url 에서 쿼리문을 반환 """
        from urllib.parse import urlparse, parse_qs

        url_info = urlparse(url)
        result = parse_qs(url_info.query)
        for key in result:
            result[key] = result[key][0]

        return result
