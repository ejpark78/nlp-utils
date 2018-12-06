#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from datetime import datetime

from module.crawler_base import CrawlerBase
from module.config import Config
from module.elasticsearch_utils import ElasticSearchUtils

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class CorpusUtils(CrawlerBase):
    """크롤링 결과 추출"""

    def __init__(self):
        """ 생성자 """
        self.job_id = 'twitter'
        self.cfg = Config(job_id=self.job_id)

        self.job_info = self.cfg.job_info['twitter_list']

    def dump(self):
        """"""
        # 데이터 덤프
        elastic_utils = ElasticSearchUtils(host=self.job_info['host'], index=self.job_info['index'],
                                           bulk_size=20)

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
