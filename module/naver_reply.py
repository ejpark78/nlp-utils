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
from urllib.parse import urljoin
from datetime import datetime
from dateutil.rrule import rrule, DAILY

import requests
import urllib3
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from time import sleep

from module.crawler_base import CrawlerBase
from module.elasticsearch_utils import ElasticSearchUtils
from module.logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(format='%(message)s')

logger = logging.getLogger()

logger.setLevel(MESSAGE)
logger.handlers = [logging.StreamHandler(sys.stderr)]


class NaverNewsReplyCrawler(CrawlerBase):
    """네이버 뉴스 댓글 수집기"""

    def __init__(self, category='', job_id='', column=''):
        """ 생성자 """
        super().__init__()

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
            for job in self.job_info:
                self.sleep_time = job['sleep']

                for url_frame in job['list']:
                    self.trace_news(url_frame=url_frame, job=job, date=dt.strftime('%Y%m%d'))

        return

    def trace_news(self, url_frame, job, date):
        """뉴스 하나를 조회한다."""
        elastic_utils = ElasticSearchUtils(
            host=job['host'],
            index=job['index'],
            bulk_size=20,
            http_auth=job['http_auth'],
        )

        query = {
            'date': date,
            'page': 1,
            'total': 500,
        }

        headers = deepcopy(self.headers['desktop'])

        while query['page'] <= query['total']:
            headers['Referer'] = url_frame['Referer'].format(**query)

            url = url_frame['list'].format(**query)
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

                news['url'] = urljoin(url_frame['list'], news['url'])

                # 댓글 조회
                news = self.get_reply(news=news, url_frame=url_frame)

                # 문서 저장
                doc_id = '{oid}-{aid}'.format(**news)
                news['_id'] = doc_id

                elastic_utils.save_document(document=news)
                elastic_utils.flush()

                msg = {
                    'level': 'MESSAGE',
                    'message': '문서 저장 성공',
                    'doc_url': '{host}/{index}/doc/{id}?pretty'.format(
                        host=elastic_utils.host,
                        index=elastic_utils.index,
                        id=doc_id,
                    ),
                    'news': news,
                }
                logger.log(level=MESSAGE, msg=LogMsg(msg))

                sleep(self.sleep_time)

            query['page'] += 1

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

        return news

    def extract_reply_list(self, base_url, query, url_frame):
        """댓글 목록을 추출해서 반환한다."""
        headers = deepcopy(self.headers['desktop'])

        headers['Referer'] = base_url

        url = url_frame['reply'].format(**query)
        resp = requests.get(url=url, headers=headers)

        query['page'] += 1

        try:
            callback = re.sub(r'_callback\((.+)\);$', r'\g<1>', resp.text)
            callback = json.loads(callback)

            comment_list = callback['result']['commentList']
        except Exception as e:
            print(e)
            return [], query['total']

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
