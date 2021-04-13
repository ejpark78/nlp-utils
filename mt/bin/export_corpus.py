#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import ssl

import pytz
import sys
import urllib3
from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context
from tqdm.autonotebook import tqdm

from logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.basicConfig(**logging_opt)

logger = logging.getLogger()


class ExportCorpus(object):
    """ """

    def __init__(self, host=None, index=None, http_auth=None):
        """ 생성자 """
        self.host = host

        self.http_auth = None
        if http_auth is not None:
            self.http_auth = (http_auth.split(':'))

        self.elastic = None

        self.index = index

        self.timezone = pytz.timezone('Asia/Seoul')

        if self.host is not None:
            self.open()

    @staticmethod
    def get_ssl_verify_mode():
        """ """
        # https://github.com/elastic/elasticsearch-py/issues/712
        ssl_context = create_ssl_context()

        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        return ssl_context

    def open(self, host=None):
        """서버에 접속한다."""
        if host is not None:
            self.host = host

        ssl_context = None
        check_verify_mode = False

        if check_verify_mode is True:
            ssl_context = self.get_ssl_verify_mode()

        # host 접속
        try:
            self.elastic = Elasticsearch(
                hosts=self.host,
                timeout=30,
                http_auth=self.http_auth,
                ssl_context=ssl_context,
            )
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '서버 접속 에러',
                'host': self.host,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))
            return

        return

    def scroll(self, index, scroll_id, query, size=1000):
        """스크롤 API를 호출한다."""
        if index is None:
            index = self.index

        params = {
            'request_timeout': 2 * 60
        }

        # 스크롤 아이디가 있다면 scroll 함수 호출
        if scroll_id == '':
            search_result = self.elastic.search(
                index=index,
                body=query,
                scroll='2m',
                size=size,
                params=params,
            )
        else:
            search_result = self.elastic.scroll(
                scroll_id=scroll_id,
                scroll='2m',
                params=params,
            )

        # 검색 결과 추출
        scroll_id = search_result['_scroll_id']

        hits = search_result['hits']

        total = hits['total']
        if isinstance(total, dict) and 'value' in total:
            total = total['value']

        count = len(hits['hits'])

        return hits['hits'], scroll_id, count, total

    def export(self, index, query=None, size=1000, result=None, limit=0):
        """데이터를 서버에서 덤프 받는다."""
        if query is None:
            query = {}
        elif isinstance(query, str):
            query = json.loads(query)

        self.index = index

        count = 1
        sum_count = 0
        scroll_id = ''

        p_bar = None

        while count > 0:
            hits, scroll_id, count, total = self.scroll(
                index=index,
                size=size,
                query=query,
                scroll_id=scroll_id,
            )

            if p_bar is None:
                p_bar = tqdm(total=total, desc='dump: ' + index, dynamic_ncols=True)

            p_bar.update(count)

            sum_count += count

            msg = {
                'level': 'INFO',
                'index': index,
                'count': count,
                'sum_count': sum_count,
                'total': total,
            }
            logger.info(msg=LogMsg(msg))

            for item in hits:
                if result is None:
                    document = json.dumps(item['_source'], ensure_ascii=False, sort_keys=True)
                    print(document, flush=True)
                else:
                    result.append(item['_source'])

            # 종료 조건
            if count < size:
                break

            if 0 < limit <= sum_count:
                break

        if p_bar is not None:
            p_bar.close()

        return

    @staticmethod
    def read_config(filename):
        """ """
        with open(filename, 'r') as fp:
            result = json.load(fp)

        return result

    @staticmethod
    def parse_lucene_query(query):
        """ """
        from luqum.elasticsearch import ElasticsearchQueryBuilder
        from luqum.parser import parser

        tree = parser.parse(query)

        es_builder = ElasticsearchQueryBuilder(not_analyzed_fields=['published', 'tag'])

        return es_builder(tree)

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        def parse_bool(x): return str(x).lower() in ['true', '1', 'yes']

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('--export', default=False, type=parse_bool, nargs='?')
        parser.add_argument('--config', default=None)

        return parser.parse_args()


def main():
    """메인"""
    args = ExportCorpus().init_arguments()

    config = ExportCorpus().read_config(filename=args.config)
    logging.log(MESSAGE, config)

    utils = ExportCorpus(host=config['host'], http_auth=config['auth'])

    if args.export is True:
        query = config['query']
        if 'search' in query:
            query['query'] = utils.parse_lucene_query(query['search'])
            del query['search']

        logging.log(MESSAGE, query)

        utils.export(
            index=config['index'],
            query=query,
            limit=config['limit'],
        )

    return


if __name__ == '__main__':
    main()
