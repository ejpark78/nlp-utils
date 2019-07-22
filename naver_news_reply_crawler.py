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

import pytz
import requests
import urllib3
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from time import sleep

from module.logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(format='%(message)s')

logger = logging.getLogger()

logger.setLevel(MESSAGE)
logger.handlers = [logging.StreamHandler(sys.stderr)]


class NaverNewsReplyCrawler(object):
    """네이버 뉴스 댓글 크롤러"""

    def __init__(self):
        """ 생성자 """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/75.0.3770.100 Safari/537.36',
        }

        self.index_url = 'https://sports.news.naver.com/kbaseball/news/index.nhn?' \
                         'isphoto=N&type=comment&date={date}&page={page}'

        self.list_url = 'https://sports.news.naver.com/kbaseball/news/list.nhn?' \
                        'isphoto=N&type=comment&page={page}&date={date}'

        self.reply_url = 'https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?' \
                         'ticket=sports&templateId=view&pool=cbox2&lang=ko&country=KR&' \
                         'objectId=news{oid},{aid}&categoryId=&pageSize=20&indexSize=10&groupId=&' \
                         'listType=OBJECT&pageType=more&page={page}&refresh=false&sort=LIKE'

        self.stop_columns = [
            'idType', 'lang', 'country', 'idProvider', 'visible', 'containText',
            'maskedUserName', 'commentType', 'expose', 'profileType', 'regTimeGmt',
            'modTimeGmt', 'templateId', 'userProfileImage',
        ]

        self.timezone = pytz.timezone('Asia/Seoul')

    def batch(self, start_date='20190719'):
        """"""
        start_date = parse_date(start_date)
        start_date = self.timezone.localize(start_date)

        while True:
            self.get_news_by_date(date=start_date.strftime('%Y%m%d'))
            start_date += relativedelta(days=-1)

    def get_news_by_date(self, date):
        """해당 날자의 모든 기사를 조회한다."""
        from module.elasticsearch_utils import ElasticSearchUtils

        elastic_utils = ElasticSearchUtils(
            host='https://corpus.ncsoft.com:9200',
            index='crawler-naver-sports-reply',
            bulk_size=1,
            http_auth='elastic:nlplab',
        )

        query = {
            'date': date,
            'page': 1,
            'total': 500,
        }

        while query['page'] <= query['total']:
            headers = deepcopy(self.headers)
            headers['Referer'] = self.index_url.format(**query)

            url = self.list_url.format(**query)
            news_info = requests.get(url=url, headers=headers).json()

            query['total'] = news_info['totalPages']
            for news in news_info['list']:
                msg = {
                    'level': 'MESSAGE',
                    'message': '기사 조회',
                    'news': news,
                    'query': query,
                }
                logger.log(level=MESSAGE, msg=LogMsg(msg))

                news['url'] = urljoin(self.list_url, news['url'])

                news = self.get_reply(news=news)

                doc_id = '{oid}-{aid}'.format(**news)
                news['_id'] = doc_id

                elastic_utils.save_document(document=news)
                elastic_utils.flush()

                msg = {
                    'level': 'MESSAGE',
                    'message': '기사 저장 성공',
                    'doc_url': '{host}/{index}/doc/{id}?pretty'.format(
                        host=elastic_utils.host,
                        index=elastic_utils.index,
                        id=doc_id,
                    ),
                    'news': news,
                }
                logger.log(level=MESSAGE, msg=LogMsg(msg))

                sleep(5)

            query['page'] += 1

        return

    def get_reply(self, news):
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

            reply_list, query['total'] = self.extract_reply_list(base_url=news['url'], query=query)
            result += reply_list

            sleep(5)

        news['reply_list'] = result

        return news

    def extract_reply_list(self, base_url, query):
        """댓글 목록을 추출해서 반환한다."""
        headers = deepcopy(self.headers)

        headers['Referer'] = base_url

        url = self.reply_url.format(**query)
        resp = requests.get(url=url, headers=headers)

        query['page'] += 1

        callback = re.sub(r'_callback\((.+)\);$', r'\g<1>', resp.text)
        callback = json.loads(callback)

        comment_list = callback['result']['commentList']

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


if __name__ == '__main__':
    NaverNewsReplyCrawler().batch()
