#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from multiprocessing import Pool, Process
from pprint import pprint

import requests
from tqdm import trange
from tqdm.autonotebook import tqdm

from module.elasticsearch_utils import ElasticSearchUtils


class CorpusPipelineUtils(object):
    """ """

    def __init__(self):
        """ """

    @staticmethod
    def get_missing_ids(source_ids, target_ids):
        """ 빠진 문서 아이디 목록을 추출한다."""
        result = []
        for doc_id in tqdm(source_ids, dynamic_ncols=True):
            if doc_id in target_ids:
                continue

            result.append(doc_id)

        return result

    @staticmethod
    def call_corpus_pipeline(doc_list, target_index, url, domain, timeout):
        """ """
        post_data = {
            "elastic": {
                "host": "https://corpus.ncsoft.com:9200",
                "index": target_index,
                "http_auth": "crawler:crawler2019",
                "split_index": True
            },
            "module": [
                {
                    "name": "nlu_wrapper",
                    "option": {
                        "domain": domain,
                        "style": "literary",
                        "module": ["SBD_crf", "POS", "NER"]
                    },
                    "column": "content",
                    "result": "nlu_wrapper"
                }
            ],
            "document": doc_list
        }

        return requests.post(url=url, json=post_data, timeout=timeout)

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-domain', default='sports', help='')
        parser.add_argument('-year', default='2019', help='')
        parser.add_argument('-nlu_domain', default='baseball', help='')
        parser.add_argument('-max_doc', default=50, type=int, help='')
        parser.add_argument('-max_core', default=32, type=int, help='')
        parser.add_argument('-timeout', default=120, type=int, help='')
        parser.add_argument('-join', default=240, type=int, help='')

        return parser.parse_args()

    def batch(self):
        """ """
        args = self.init_arguments()

        host = 'https://crawler:crawler2019@corpus.ncsoft.com:9200'

        corpus_pipeline_url = 'http://172.20.78.250:20000/v1.0/batch'

        domain = args.domain
        year = args.year

        nlu_domain = args.nlu_domain

        source_index = 'crawler-naver-{}-{}'.format(domain, year)
        target_index = 'corpus_process-naver-{}-{}'.format(domain, year)

        elastic_utils = ElasticSearchUtils(host=host, index=source_index)

        # crawler-naver-economy-2019 문서 목록 덤프
        source_ids = elastic_utils.get_id_list(index=source_index)

        # corpus_process-naver-economy-2019 문서 목록 덤프
        target_ids = elastic_utils.get_id_list(index=target_index)

        # missing docs 목록 생성
        missing_ids = self.get_missing_ids(
            source_ids=source_ids,
            target_ids=target_ids,
        )

        info = {
            'missing_ids': '{:,}'.format(len(missing_ids)),
            'source_ids': '{:,}'.format(len(source_ids)),
            'target_ids': '{:,}'.format(len(target_ids)),
        }

        pprint(info)

        # 문서 본문을 가져와서 Corpus Pipeline 에 전달
        step = args.max_doc
        size = len(missing_ids)

        count = 0
        max_core = args.max_core

        proc_list = []

        for i in trange(0, size, step, dynamic_ncols=True):
            st, en = (i, i + step - 1)
            if en > size:
                en = size + 1

            doc_list = []
            elastic_utils.get_by_ids(
                id_list=missing_ids[st:en],
                index=source_index,
                source=None,
                result=doc_list,
            )

            proc = Process(
                target=self.call_corpus_pipeline,
                args=(doc_list, target_index, corpus_pipeline_url, nlu_domain, args.timeout, )
            )
            proc_list.append(proc)
            proc.start()

            count += 1
            if count > max_core:
                count = 0

                for proc in proc_list:
                    proc.join(args.join)

        return


if __name__ == '__main__':
    utils = CorpusPipelineUtils()

    utils.batch()

