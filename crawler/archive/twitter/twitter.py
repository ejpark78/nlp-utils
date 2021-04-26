#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep

import requests
import urllib3
from bs4 import BeautifulSoup
from requests_oauthlib import OAuth1Session

from crawler.web_news.base import WebNewsBase
from crawler.utils.es import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class TwitterCrawler(WebNewsBase):
    """트위터 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.job_category = 'sns'
        self.job_id = 'twitter'
        self.column = 'trace_list'

        self.max_error_count = 0

    def get_category(self, category):
        """카테고리 하위 목록을 크롤링한다."""
        job_info = self.job_info
        twitter = OAuth1Session(job_info['api']['key'],
                                client_secret=job_info['api']['secret'],
                                resource_owner_key=job_info['access_token']['token'],
                                resource_owner_secret=job_info['access_token']['secret'])

        url_frame = job_info['url_frame']['user_timeline']
        url = url_frame.format(screen_name=category['id'])

        resp = twitter.get(url)
        self.sleep()

        self.max_error_count = 10

        tweet_list = resp.json()
        for tweet in tweet_list:
            # tweet 저장 및 댓글 조회
            self.get_reply(screen_name=category['id'], tweet=tweet)

            if self.max_error_count < 0:
                break

            # 현재 크롤링 위치 저장
            self.status['category'] = category

        # 크롤링 위치 초기화
        del self.status['category']

        return

    def get_reply(self, screen_name, tweet):
        """트윗에 대한 댓글을 조회한다."""
        if isinstance(tweet, str):
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '트윗 댓글 조회 에러',
                'tweet': tweet,
            })
            return

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

        resp = None
        try:
            resp = requests.get(url, headers=headers, verify=False)
            reply = resp.json()
        except Exception as e:
            if resp is not None:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '트윗 댓글 조회: resp 가 없음',
                    'exception': str(e),
                })

            self.max_error_count -= 1

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '트윗 댓글 조회: 슬립',
                'max_error_count': self.max_error_count,
                'screen_name': screen_name,
                'url': url,
                'sleep': 10,
            })

            sleep(10)
            return

        # 댓글 저장
        if 'page' in reply:
            self.save_tweet(tweet, reply['page'], base_url=url)

        self.sleep()
        return

    def save_tweet(self, tweet, reply_page, base_url):
        """트윗과 댓글을 저장한다."""
        job_info = self.job_info
        parsing_info = self.parsing_info
        trace_tag = parsing_info['trace']['tag']

        elastic_utils = ElasticSearchUtils(
            host=job_info['host'],
            index=job_info['index'],
            bulk_size=20,
            http_auth=job_info['http_auth'],
        )

        soup = BeautifulSoup(reply_page, 'html5lib')

        unique_tweet = {}

        for trace in trace_tag:
            item_list = soup.find_all(trace['name'], trace['attribute'])
            for item in item_list:
                # html 본문에서 값 추출
                values = self.parser.parse(
                    html=None,
                    soup=item,
                    parsing_info=parsing_info['values'],
                    base_url=base_url,
                )

                tweet_id = tweet['id']
                if tweet_id in unique_tweet:
                    continue
                unique_tweet[tweet_id] = 1

                k0, doc = self.merge_values(values)

                tweet['_id'] = tweet_id
                if k0 != '':
                    tweet[k0] = doc

                # 이전에 수집한 문서와 병합
                tweet = self.merge_doc(elastic_utils=elastic_utils, index=job_info['index'], tweet=tweet)

                # 현재 상태 로그 표시
                reply_list = []
                if 'reply' in tweet:
                    reply_list = tweet['reply']

                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '트윗 저장 성공',
                    'id': tweet['id'],
                    'text': tweet['text'],
                    'reply': reply_list,
                })

                # 문서 저장
                elastic_utils.save_document(document=tweet)

            elastic_utils.flush()

        return

    def merge_doc(self, elastic_utils, index, tweet):
        """이전에 수집한 문서와 병합"""
        tweet_id = tweet['id']

        exists = elastic_utils.conn.exists(index=index, id=tweet_id)
        if exists is False:
            return tweet

        doc = elastic_utils.conn.get(index=index, id=tweet_id)
        if '_source' not in doc:
            return tweet

        prev_tweet = doc['_source']

        if 'reply' in prev_tweet and 'reply' in tweet:
            tweet['reply'] = self.merge_reply(prev_tweet['reply'], tweet['reply'])

        # 문서 병합
        prev_tweet.update(tweet)

        return prev_tweet

    @staticmethod
    def merge_reply(prev_reply, reply):
        """댓글을 합친다."""
        from operator import eq

        new_data = []
        for item in reply:
            if eq(item, prev_reply[0]) is True:
                break

            new_data.append(item)

        return new_data + prev_reply

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

    def sleep(self):
        """잠시 쉰다."""
        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '슬립',
            'sleep_time': self.sleep_time
        })

        sleep(self.sleep_time)
        return

    def batch(self):
        """카테고리 하위 목록을 크롤링한다."""
        self.update_config(filename=None, job_id=self.job_id, job_category=self.job_category, column=self.env.column)

        # 이전 카테고리를 찾는다.
        category_id = None
        if 'category' in self.status:
            category_id = self.status['category']['id']

        # 카테고리 하위 목록을 크롤링한다.
        category_list = self.job_info['category']
        for c in category_list:
            if category_id is not None and c['id'] != category_id:
                continue

            category_id = None
            self.get_category(category=c)

        return


if __name__ == '__main__':
    TwitterCrawler().batch()
