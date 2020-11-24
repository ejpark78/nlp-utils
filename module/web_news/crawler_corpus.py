#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
from datetime import datetime
from glob import glob
from io import BufferedReader
from time import sleep
from uuid import uuid1

import urllib3
from dateutil.parser import parse as parse_date
from tqdm import tqdm

from utils.elasticsearch_utils import ElasticSearchUtils
from module.web_news.web_news import WebNewsCrawler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CrawlerCorpus(WebNewsCrawler):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self, category='', job_id='', column=''):
        """ 생성자 """
        super().__init__(category=category, job_id=job_id, column=column)

    def generate_cmd(self, data_dir):
        """실행 스크립트를 생성한다."""
        self.big3_mongo(data_dir=data_dir)

        return

    def bbs(self):
        """bbs"""
        host_idx = 0
        host_list = 'nlp-w7,nlp-w8,nlp-w9,nlp-w10,nlp-w11,nlp-w12,nlp-w13'.split(',')

        home = '/home/ejpark/workspace/data-center/data/dump/mongodb/crawler/crawler.2019-03-18'
        data_dir = '{home}/mlbpark_bullpen'.format(home=home)

        category = 'bbs'
        job_id = 'mlbpark-bullpen'

        f_list = glob('{data_dir}/*.json.bz2'.format(data_dir=data_dir))
        for filename in sorted(f_list):
            f_name = filename.split('/')[-1]
            if f_name[0] != '2' and f_name[0] != '1':
                continue

            uid = uuid1()
            share = '/home/ejpark/tmp'

            host = host_list[host_idx]
            host_idx += 1
            if host_idx >= len(host_list):
                host_idx = 0

            query = {
                'filename': filename,
                'host': host,
                'uid': uid,
                'share': share,
                'category': category,
                'job_id': job_id,
            }

            print(self.get_cmd_str(query=query))

        return

    @staticmethod
    def get_cmd_str(query):
        """쉘 커멘드를 반환한다."""
        use_docker = False

        if use_docker is True:
            scp = 'scp {filename} {host}:{share}/{uid}.json.bz2'.format(**query)

            docker = 'docker -H {host}:2376 ' \
                     'run ' \
                     '--label task=crawler_corpus ' \
                     '-v {share}:/usr/local/app/data:rw ' \
                     'registry.nlp-utils/crawler:latest'.format(**query)

            cmd = 'PYTHONPATH=. python3 module/crawler_corpus.py ' \
                  '-update_corpus ' \
                  '-category {category} ' \
                  '-job_id {job_id} ' \
                  '-filename data/{uid}.json.bz2'.format(**query)
        else:
            cmd = 'PYTHONPATH=. python3 module/crawler_corpus.py ' \
                  '-update_corpus ' \
                  '-category {category} ' \
                  '-job_id {job_id} ' \
                  '-filename {filename}'.format(**query)

            return cmd

        return '{scp} && {docker} {cmd}'.format(scp=scp, docker=docker, cmd=cmd)

    def big3_mongo(self, data_dir):
        """big3"""
        host_idx = 0
        host_list = 'nlp-w7,nlp-w8,nlp-w9,nlp-w10,nlp-w11,nlp-w12,nlp-w13'.split(',')

        for category in ['naver', 'nate', 'daum']:
            d_list = glob('{data_dir}/{category}*'.format(data_dir=data_dir, category=category))
            for dir_name in sorted(d_list):
                if dir_name.find('.done') > 0 or dir_name.find('.error') > 0:
                    continue

                job_id = dir_name.split('_')[-1]

                f_list = glob(
                    '{dir_name}/*.json.bz2'.format(
                        dir_name=dir_name,
                    )
                )

                for filename in f_list:
                    f_name = filename.split('/')[-1]
                    if f_name[0] != '2' and f_name[0] != '1':
                        continue

                    uid = uuid1()
                    share = '/home/ejpark/tmp'

                    host = host_list[host_idx]
                    host_idx += 1
                    if host_idx >= len(host_list):
                        host_idx = 0

                    query = {
                        'filename': filename,
                        'host': host,
                        'uid': uid,
                        'share': share,
                        'category': category,
                        'job_id': job_id,
                    }

                    print(self.get_cmd_str(query=query))

        return

    @staticmethod
    def read_corpus(filename):
        """파일을 읽어서 반환한다."""
        result = []
        with bz2.open(filename=filename, mode='rb') as fp:
            bfp = BufferedReader(fp)

            for line in tqdm(bfp.readlines()):
                try:
                    result.append(json.loads(line))
                except Exception as e:
                    log_msg = {
                        'task': 'load json',
                        'message': 'JSON 변환 오류',
                        'line': line,
                        'exception': str(e),
                    }
                    logging.error(msg=log_msg)

        return result

    @staticmethod
    def json_default(value):
        """ 입력받은 문서에서 데이터 타입이 datetime 를 문자열로 변환한다."""
        if isinstance(value, datetime):
            return value.isoformat()

        raise TypeError('not JSON serializable')

    def get_url_str(self, url):
        """url 문자열을 반환한다."""
        if isinstance(url, dict) and 'full' in url:
            url = self.get_url_str(url=url['full'])

        return url

    def update_article(self, doc, job, id_idx, index):
        """문서를 업데이트 한다."""
        doc['url'] = self.get_url_str(url=doc['url'])

        # 날짜 변환
        for k in ['date', 'curl_date']:
            if k not in doc:
                continue

            if isinstance(doc[k], dict):
                doc[k] = doc[k]['$date']

            dt = parse_date(doc[k])
            doc[k] = dt.astimezone(self.timezone)

        # 필드 삭제
        for k in ['photo_list', 'photo_caption']:
            if k in doc:
                del doc[k]

        # 필드명 변경
        if 'replay_list' in doc:
            doc['reply_list'] = doc['replay_list']
            del doc['replay_list']

        if 'document_id' in doc:
            del doc['document_id']

        # 문서 아이디 중복 점검
        doc['_id'] = self.get_doc_id(url=doc['url'], job=job, item=doc)
        if doc['_id'] in id_idx[index]:
            return {'error': 'doc id exits'}, None

        article_url = None
        if 'article' in job:
            article_url = job['article']
            article_url['url'] = doc['url']

        if 'raw_html' in doc:
            resp = doc['raw_html']
        else:
            if 'html_content' not in doc:
                return {'error': 'html_content not found'}, None

            resp = doc['html_content']

        # mlbpark 의 경우
        if index.find('mlbpark') >= 0:
            if 'reply_list' in doc and isinstance(doc['reply_list'], str):
                resp += doc['reply_list']
                del doc['reply_list']

        article = self.parse_tag(
            resp=resp,
            base_url=doc['url'],
            url_info=article_url,
            parsing_info=self.parsing_info['article'],
        )

        return {'ok': 'ok'}, article

    def update_corpus(self, filename, target_host='https://nlp.ncsoft.com:9200', auth='elastic:nlplab'):
        """image_list, cdn_image 필드를 업데이트 한다. html_content 를 재파싱한다."""
        import shutil
        from os import makedirs
        from os.path import basename, dirname, isdir

        self.update_config()

        if self.parsing_info is None:
            return

        print('filename: ', filename)

        id_idx = {}

        for job in self.job_info:
            index = job['index']

            job['host'] = target_host
            job['http_auth'] = auth

            elastic_utils = ElasticSearchUtils(
                host=job['host'],
                index=job['index'],
                bulk_size=100,
                http_auth=job['http_auth'],
            )

            if index not in id_idx:
                id_idx[index] = elastic_utils.get_id_list(index=index)

            # 문서 로딩
            doc_list = self.read_corpus(filename=filename)

            is_error = False
            for doc in tqdm(doc_list, desc=basename(filename), dynamic_ncols=True):
                state, article = self.update_article(
                    doc=doc,
                    job=job,
                    index=index,
                    id_idx=id_idx,
                )

                if 'error' in state:
                    continue

                # 문서 저장
                if article is None:
                    is_error = True
                    continue

                if len(article) == 0:
                    # 삭제된 기사
                    continue

                article = self.parser.merge_values(item=article)
                doc.update(article)

                if 'date' not in doc:
                    is_error = True
                    continue

                # 문서 저장: elasticsearch
                index = '{index}-{year}'.format(
                    year=doc['date'].year,
                    index=job['index'],
                )

                if index not in id_idx:
                    id_idx[index] = elastic_utils.get_id_list(index=index)

                elastic_utils.save_document(document=doc, index=index, delete=False)

            elastic_utils.flush()

            # done 처리
            done_path = dirname(filename) + '.done'
            if is_error is True:
                done_path = dirname(filename) + '.error'

            if isdir(done_path) is False:
                makedirs(done_path)

            shutil.move(filename, done_path + '/' + basename(filename))

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
                index=job['index'],
                date_range=date_range,
                query_field=query_field,
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
                article, article_html = self.get_article(
                    job=job,
                    item=item,
                    doc_id=doc_id,
                    offline=True,
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

                self.logger.info(msg={
                    'level': 'INFO',
                    'message': '뉴스 본문 크롤링: 슬립',
                    'sleep_time': self.sleep_time,
                })

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
    parser.add_argument('-date_range', default=None, help='date 날짜 범위: 2000-01-01~2019-04-10')
    parser.add_argument('-query_field', default='date', help='query field')

    parser.add_argument('-filename', default='', help='코퍼스 파일명')
    parser.add_argument('-data_dir', default='', help='덤프 폴더')

    parser.add_argument('-generate_cmd', action='store_true', default=False, help='')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    if args.generate_cmd:
        CrawlerCorpus().generate_cmd(data_dir=args.data_dir)
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
