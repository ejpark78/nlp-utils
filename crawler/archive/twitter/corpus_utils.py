#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime

from crawler.web_news.base import WebNewsBase
from crawler.utils.es import ElasticSearchUtils


class CorpusUtils(WebNewsBase):
    """크롤링 결과 추출"""

    def __init__(self):
        super().__init__()

        self.job_id = 'twitter'
        self.cfg = Config(job_category='', job_id=self.job_id)

        self.job_info = self.cfg.job_info['twitter_list']

    def dump(self):
        # 데이터 덤프
        elastic_utils = ElasticSearchUtils(
            host=self.job_info['host'],
            index=self.job_info['index'],
            bulk_size=20,
            http_auth=self.job_info['http_auth'],
        )

        doc_list = elastic_utils.dump()

        # 카테고리별로 분리
        data = {}
        for doc in doc_list:
            user_name = doc['user']['name']

            if user_name not in data:
                data[user_name] = []

            item = {
                'user_name': user_name,
                'tweet_id': doc['id'],
                'tweet_text': doc['text']
            }

            if 'reply' in doc:
                for reply in doc['reply']:
                    reply['reply_name'] = reply['name']
                    reply['reply_text'] = reply['text']

                    reply.update(item)

                    data[user_name].append(reply)
            else:
                data[user_name].append(item)

        # 데이터 저장
        date_tag = datetime.now().strftime('%Y-%m-%d')

        columns = ['user_name', 'tweet_id', 'tweet_text', 'reply_name', 'reply_text']
        # self.save_excel(filename='{}-{}.xlsx'.format(self.job_info['index'], date_tag),
        #                 data=data, columns=columns)
        return
