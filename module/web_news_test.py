#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

import urllib3
from time import sleep

from module.utils.elasticsearch_utils import ElasticSearchUtils
from module.utils.logger import LogMessage as LogMsg
from module.web_news import WebNewsCrawler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logger = logging.getLogger()


class WebNewsCrawlerTest(WebNewsCrawler):
    """웹 뉴스 크롤러 테스터"""

    def __init__(self, category='', job_id='', column=''):
        """ 생성자 """
        super().__init__(category=category, job_id=job_id, column=column)

    def test(self):
        """디버그"""
        self.update_config()

        job = self.job_info[0]

        elastic_utils = ElasticSearchUtils(
            host=job['host'],
            index=job['index'],
            bulk_size=20,
            http_auth=job['http_auth'],
        )

        item = {
            'url': 'http://sports.chosun.com/news/news.htm?id=201905150100105140006997&ServiceDate=20190514',
        }

        doc_id = self.get_doc_id(url=item['url'], job=job, item=item)
        article, article_html = self.get_article(
            job=job,
            item=item,
            doc_id=doc_id,
            offline=False,
        )

        # 기사 저장
        if article is not None:
            self.save_article(
                doc=item,
                html=article_html,
                article=article,
                elastic_utils=elastic_utils,
            )

        return

    def re_crawl(self, date_range, query, query_field):
        """elasticsearch의 url 목록을 다시 크롤링한다."""
        from tqdm import tqdm

        self.update_config()

        for job in self.job_info:
            elastic_utils = ElasticSearchUtils(
                host=job['host'],
                index=job['index'],
                bulk_size=20,
                http_auth=job['http_auth'],
            )

            doc_list = elastic_utils.get_url_list(
                query=query,
                query_field=query_field,
                index=job['index'],
                date_range=date_range,
            )

            for item in tqdm(doc_list):
                for k in ['photo_list', 'photo_caption', 'edit_date']:
                    if k in item:
                        del item[k]

                doc_id = item['document_id']

                # 기사 본문 조회
                article, article_html = self.get_article(
                    doc_id=doc_id,
                    item=item,
                    job=job,
                    offline=False,
                )

                # 기사 저장
                if article is not None:
                    self.save_article(
                        doc=item,
                        html=article_html,
                        article=article,
                        elastic_utils=elastic_utils,
                    )

                # 후처리 작업 실행
                if 'post_process' not in job:
                    job['post_process'] = None

                self.post_process_utils.insert_job(
                    job=job,
                    document=article,
                    post_process_list=job['post_process'],
                )

                msg = {
                    'level': 'INFO',
                    'message': '뉴스 본문 크롤링: 슬립',
                    'sleep_time': self.sleep_time,
                }
                logger.info(msg=LogMsg(msg))

                sleep(self.sleep_time)

        return
