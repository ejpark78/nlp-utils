#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
from io import BufferedReader

import urllib3
from time import sleep
from tqdm import tqdm
from dateutil.parser import parse as parse_date
from module.elasticsearch_utils import ElasticSearchUtils
from module.logging_format import LogMessage as LogMsg
from module.web_news import WebNewsCrawler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logger = logging.getLogger()


class CrawlerCorpus(WebNewsCrawler):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self, category='', job_id='', column=''):
        """ 생성자 """
        super().__init__(category=category, job_id=job_id, column=column)

    @staticmethod
    def read_corpus(filename):
        """파일을 읽어서 반환한다."""
        result = []
        with bz2.open(filename=filename, mode='rb') as fp:
            bfp = BufferedReader(fp)

            for line in tqdm(bfp.readlines()):
                result.append(json.loads(line))

        return result

    def update_corpus(self, filename):
        """image_list, cdn_image 필드를 업데이트 한다. html_content 를 재파싱한다."""
        self.update_config()

        for job in self.job_info:
            job['host'] = 'https://nlp.ncsoft.com:9200'
            job['http_auth'] = 'elastic:nlplab'

            elastic_utils = ElasticSearchUtils(
                host=job['host'],
                index=job['index'],
                bulk_size=100,
                http_auth=job['http_auth'],
            )

            doc_list = self.read_corpus(filename=filename)

            for doc in tqdm(doc_list):
                if isinstance(doc['url'], dict):
                    doc['url'] = doc['url']['full']

                # 필드 삭제
                for k in ['date', 'curl_date']:
                    if k not in doc:
                        continue

                    if isinstance(doc[k], dict):
                        doc[k] = doc[k]['$date']

                    dt = parse_date(doc[k])
                    doc[k] = dt.astimezone(self.timezone)

                if 'document_id' in doc:
                    del doc['document_id']

                doc['_id'] = self.get_doc_id(url=doc['url'], job=job, item=doc)

                article_url = None
                if 'article' in job:
                    article_url = job['article']
                    article_url['url'] = doc['url']

                if 'raw_html' in doc:
                    resp = doc['raw_html']
                else:
                    resp = doc['html_content']

                # 문서 저장
                article = self.parse_tag(
                    resp=resp,
                    base_url=doc['url'],
                    url_info=article_url,
                    parsing_info=self.parsing_info['article'],
                )

                if article is not None:
                    doc.update(article)

                # 문서 저장
                index = '{}-{}'.format(job['index'], doc['date'].year)
                elastic_utils.save_document(document=doc, index=index, delete=False)

            elastic_utils.flush()

        return

    def update_parsing_info(self, date_range, query, query_field):
        """image_list, cdn_image 필드를 업데이트 한다. html_content 를 재파싱한다."""
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
                if 'image_list' not in item:
                    continue

                # 필드 삭제
                for k in ['photo_list', 'photo_caption', 'edit_date']:
                    if k in item:
                        del item[k]

                doc_id = item['document_id']

                # 기사 본문 조회
                article = self.get_article(
                    doc_id=doc_id,
                    item=item,
                    job=job,
                    elastic_utils=elastic_utils,
                    offline=True,
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


def init_arguments():
    """ 옵션 설정 """
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('-update_corpus', action='store_true', default=False, help='데이터 업데이트')
    parser.add_argument('-update_parsing_info', action='store_true', default=False, help='데이터 업데이트')

    # 작업 아이디
    parser.add_argument('-category', default='', help='작업 카테고리')
    parser.add_argument('-job_id', default='', help='작업 아이디')

    parser.add_argument('-query', default='', help='elasticsearch query')
    parser.add_argument('-date_range', default='', help='date 날짜 범위: 2000-01-01~2019-04-10')
    parser.add_argument('-query_field', default='date', help='query field')

    parser.add_argument('-filename', default='', help='코퍼스 파일명')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    if args.update_corpus:
        CrawlerCorpus(
            category=args.category,
            job_id=args.job_id,
            column='trace_list',
        ).update_corpus(
            filename=args.filename,
        )
        return

    if args.update_parsing_info:
        CrawlerCorpus(
            category=args.category,
            job_id=args.job_id,
            column='trace_list',
        ).update_parsing_info(
            query=args.query,
            date_range=args.date_range,
            query_field=args.query_field,
        )
        return

    return


if __name__ == '__main__':
    main()
