#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from time import sleep

import requests
import urllib3
from bs4 import BeautifulSoup
from requests_oauthlib import OAuth1Session

from module.common_utils import CommonUtils
from module.config import Config
from module.elasticsearch_utils import ElasticSearchUtils
from module.html_parser import HtmlParser

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class TwitterUtils(object):
    """트위터 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_id = 'twitter'
        column = 'twitter_list'

        self.common_utils = CommonUtils()
        self.parser = HtmlParser()

        self.cfg = Config(job_id=self.job_id)

        # request 헤더 정보
        self.headers = self.cfg.headers

        # html 파싱 정보
        self.parsing_info = self.cfg.parsing_info['reply_list']

        # crawler job 정보
        self.job_info = self.cfg.job_info[column]
        self.sleep = self.job_info['sleep']

        # 크롤링 상태 정보
        self.status = self.cfg.status[column]

    def batch(self):
        """카테고리 하위 목록을 크롤링한다."""
        # 이전 카테고리를 찾는다.
        category_id = None
        if 'category' in self.status:
            category_id = self.status['category']['id']

        # 카테고리 하위 목록을 크롤링한다.
        for c in self.job_info['category']:
            if category_id is not None and c['id'] != category_id:
                continue

            category_id = None
            self.get_category(category=c)

        return

    def get_category(self, category):
        """카테고리 하위 목록을 크롤링한다."""
        twitter = OAuth1Session(self.job_info['api']['key'],
                                client_secret=self.job_info['api']['secret'],
                                resource_owner_key=self.job_info['access_token']['token'],
                                resource_owner_secret=self.job_info['access_token']['secret'])

        url_frame = 'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name={screen_name}'
        url = url_frame.format(screen_name=category['id'])

        resp = twitter.get(url)
        sleep(1)

        tweet_list = resp.json()
        for tweet in tweet_list:
            # tweet 저장 및 댓글 조회
            self.get_reply(screen_name=category['id'], tweet=tweet)

            # 현재 크롤링 위치 저장
            self.status['category'] = category

            self.cfg.save_status()

        return

    def get_reply(self, screen_name, tweet):
        """트윗에 대한 댓글을 조회한다."""
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate, br',
            'referer': 'https://twitter.com/{0}'.format(screen_name),
            'x-overlay-request': 'true',
            'x-previous-page-name': 'profile',
            'x-requested-with': 'XMLHttpRequest',
            'x-twitter-active-user': 'yes'
        }

        url_frame = 'https://twitter.com/{}/status/{}?conversation_id={}'
        url = url_frame.format(screen_name, tweet['id'], tweet['id'])

        resp = requests.get(url, headers=headers)
        reply = resp.json()

        # 댓글 저장
        if 'page' in reply:
            self.save_tweet(tweet, reply['page'])

        sleep(1)
        return

    def save_tweet(self, tweet, reply_page):
        """"""
        trace_tag = self.parsing_info['trace']['tag']

        elastic_utils = ElasticSearchUtils(host=self.job_info['host'], index=self.job_info['index'],
                                           bulk_size=20)

        soup = BeautifulSoup(reply_page, 'html5lib')

        uniq_tweet = {}

        for trace in trace_tag:
            item_list = soup.find_all(trace['name'], trace['attribute'])
            for item in item_list:
                # html 본문에서 값 추출
                values = self.parser.parse(html=None, soup=item,
                                           parsing_info=self.parsing_info['values'])

                if tweet['id'] in uniq_tweet:
                    continue
                uniq_tweet[tweet['id']] = 1

                k0, doc = self.merge_values(values)

                tweet['_id'] = tweet['id']
                if k0 != '':
                    tweet[k0] = doc

                # 현재 상태 로그 표시
                msg = '{} {}'.format(tweet['id'], tweet['text'])
                if 'reply' in tweet:
                    msg = '{} {} {}'.format(tweet['id'], tweet['text'], tweet['reply'])

                logging.info(msg=msg)

                elastic_utils.save_document(document=tweet)

            elastic_utils.flush()

        return

    @staticmethod
    def merge_values(doc):
        """배열 형태의 댓글을 dictionary 형태로 변환한다."""
        max_size = 0
        for k in doc:
            if isinstance(doc[k], list):
                max_size = len(doc[k])
            elif isinstance(doc[k], str):
                max_size = 1

            break

        k0 = ''

        result = []
        for i in range(max_size):
            item = {}
            for k in doc:
                token = k.split('.', maxsplit=1)

                k0 = token[0]
                k1 = token[1]

                if len(doc[k]) > i:
                    item[k1] = doc[k][i]

            result.append(item)

        return k0, result
