#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
from io import BufferedReader
from time import sleep

import urllib3
from dateutil.parser import parse as parse_date
from tqdm import tqdm

from module.elasticsearch_utils import ElasticSearchUtils
from module.logging_format import LogMessage as LogMsg
from module.sqlite_utils import SqliteUtils
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
    def generate_cmd():
        """"""
        from uuid import uuid1
        from glob import glob

        host_idx = 0
        host_list = 'g1,g2,g3,g4,g5,g7'.split(',')

        data_dir = '/home/ejpark/workspace/data-center/data/dump/mongodb/crawler/crawler.2019-03-18'

        for site in ['naver']:
            d_list = glob('{data_dir}/{site}_*'.format(data_dir=data_dir, site=site))
            for d in d_list:
                d = d.split('_')[-1]

                f_list = glob(
                    '{data_dir}/{site}_{d}/2*-*.json.bz2'.format(
                        data_dir=data_dir,
                        site=site,
                        d=d,
                    )
                )

                for f in f_list:
                    uid = uuid1()
                    share = '/home/ejpark/tmp'

                    host = host_list[host_idx]
                    host_idx += 1
                    if host_idx >= len(host_list):
                        host_idx = 0

                    query = {
                        'f': f,
                        'host': host,
                        'uid': uid,
                        'share': share,
                        'site': site,
                        'd': d,
                    }

                    scp = 'scp {f} {host}:{share}/{uid}.json.bz2'.format(**query)

                    docker = 'docker -H {host}:2376 run ' \
                             '--label task=crawler_corpus ' \
                             '-v {share}:/usr/local/app/data:rw ' \
                             'corpus:5000/crawler:latest'.format(**query)

                    cmd = 'python3 crawler_corpus.py ' \
                          '-update_corpus ' \
                          '-category {site} ' \
                          '-job_id {d} ' \
                          '-filename data/{uid}.json.bz2'.format(**query)

                    print('{scp} && {docker} {cmd}'.format(scp=scp, docker=docker, cmd=cmd))

        return

    @staticmethod
    def read_corpus(filename):
        """파일을 읽어서 반환한다."""
        result = []
        with bz2.open(filename=filename, mode='rb') as fp:
            bfp = BufferedReader(fp)

            for line in tqdm(bfp.readlines()):
                result.append(json.loads(line))

        return result

    @staticmethod
    def json_default(value):
        """ 입력받은 문서에서 데이터 타입이 datetime 를 문자열로 변환한다."""
        from datetime import datetime

        if isinstance(value, datetime):
            return value.isoformat()

        raise TypeError('not JSON serializable')

    def update_corpus(self, filename):
        """image_list, cdn_image 필드를 업데이트 한다. html_content 를 재파싱한다."""
        self.update_config()

        if self.parsing_info is None:
            return

        tbl_info = {
            'name': 'tbl',
            'primary': 'raw',
            'columns': ['id', 'raw'],
        }

        db = {}

        for job in self.job_info:
            # job['host'] = 'https://nlp.ncsoft.com:9200'
            # job['http_auth'] = 'elastic:nlplab'

            # elastic_utils = ElasticSearchUtils(
            #     host=job['host'],
            #     index=job['index'],
            #     bulk_size=100,
            #     http_auth=job['http_auth'],
            # )

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

                # 문서 저장: sqlite
                if article is not None:
                    doc.update(article)

                if 'date' not in doc or article is None:
                    index = 'data/{index}-error-{filename}.db'.format(
                        index=job['index'],
                        filename=filename.replace('.json.bz2', '').split('/')[-1],
                    )
                else:
                    index = 'data/{index}-{year}-{month}.db'.format(
                        index=job['index'],
                        year=doc['date'].year,
                        month=doc['date'].month,
                    )

                if index not in db:
                    db[index] = SqliteUtils(filename=index)
                    db[index].create_table(tbl_info=tbl_info)

                d = {
                    'id': doc['_id'],
                    'raw': json.dumps(doc, ensure_ascii=False, default=self.json_default),
                }
                db[index].save_doc(doc=d, tbl_info=tbl_info)

                # 문서 저장: elasticsearch
            #     index = '{}-{}'.format(job['index'], doc['date'].year)
            #     elastic_utils.save_document(document=doc, index=index, delete=False)
            #
            # elastic_utils.flush()

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

    parser.add_argument('-generate_cmd', action='store_true', default=False, help='')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    if args.generate_cmd:
        CrawlerCorpus().generate_cmd()
        return

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
