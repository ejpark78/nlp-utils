#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys

import urllib3
from tqdm.autonotebook import tqdm

from utils.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)

logger = logging.getLogger()


class RemoveDubUtils(object):
    """ """

    def __init__(self):
        """ """
        self.query = {
            '_source': ['document_id', 'title', 'date', 'content'],
        }

    def export(self, index, elastic_utils):
        """ """
        result = {'corpus': []}

        elastic_utils.export(
            query=self.query,
            index=index,
            result=result['corpus'],
        )

        for y in ['2018', '2019']:
            result[y] = []

            elastic_utils.export(
                query=self.query,
                index=index + '-' + y,
                result=result[y],
            )

        return result

    @staticmethod
    def make_idx(doc_list, tag, result):
        """ """
        for d in tqdm(doc_list, desc=tag):
            doc_id = d['document_id']
            result[doc_id] = d

        return result

    @staticmethod
    def delete_docs(elastic_utils, bulk_data, index):
        """ """
        params = {'request_timeout': 2 * 60}

        resp = elastic_utils.elastic.bulk(
            index=index,
            body=bulk_data,
            refresh=True,
            params=params,
        )

        if resp['errors'] is True:
            print(resp)

        return

    def remove_dup_section(self, section, elastic_utils):
        """ """
        index = 'crawler-naver-' + section

        # 코퍼스 덤프
        result = self.export(
            index=index,
            elastic_utils=elastic_utils,
        )

        # 인덱스 생성
        idx = {}
        for i in ['2018', '2019']:
            self.make_idx(
                tag=i,
                result=idx,
                doc_list=result[i],
            )

        # 중복 아이디 삭제
        bulk_data = []

        for d in tqdm(result['corpus'], desc=index):
            if d['document_id'] not in idx:
                continue

            bulk_data.append({
                'delete': {
                    '_index': index,
                    '_id': d['document_id'],
                }
            })

            if len(bulk_data) > 1000:
                self.delete_docs(
                    index=index,
                    bulk_data=bulk_data,
                    elastic_utils=elastic_utils,
                )
                bulk_data = []

        self.delete_docs(
            index=index,
            bulk_data=bulk_data,
            elastic_utils=elastic_utils,
        )

        return

    def batch(self):
        """ """
        host = 'https://crawler:crawler2019@corpus.ncsoft.com:9200'
        elastic_utils = ElasticSearchUtils(host=host)

        for section in ['sports', 'tv', 'politics', 'opinion', 'living', 'society', 'it', 'international']:
            self.remove_dup_section(
                section=section,
                elastic_utils=elastic_utils,
            )
        return
