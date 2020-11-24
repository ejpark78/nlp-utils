#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from multiprocessing import Pool
from pprint import pprint

import requests
from tqdm import trange
from tqdm.autonotebook import tqdm

from utils.elasticsearch_utils import ElasticSearchUtils


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
    def call_corpus_pipeline(doc_list, target_host, http_auth, target_index, url, domain, timeout):
        """ """
        post_data = {
            "elastic": {
                "host": target_host,
                "http_auth": http_auth,
                "index": target_index,
                "split_index": True
            },
            "module": [
                {
                    "name": "nlu_wrapper",
                    "option": {
                        "style": "literary",
                        "domain": domain,
                        "module": ["SBD_crf", "POS", "NER"]
                    },
                    "column": "content",
                    "result": "nlu_wrapper"
                }
            ],
            "document": doc_list
        }

        headers = {"Content-Type": "application/json"}
        resp = requests.post(url=url, json=post_data, headers=headers, timeout=timeout, verify=False)

        return resp

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-source_host', default='https://corpus.ncsoft.com:9200', help='')
        parser.add_argument('-target_host', default='https://corpus.ncsoft.com:9200', help='')

        parser.add_argument('-source_index', default='crawler-naver-economy-2020', help='')
        parser.add_argument('-target_index', default='corpus_process-naver-economy-2020', help='')
        parser.add_argument('-http_auth', default='crawler:crawler2019', help='')

        parser.add_argument('-nlu_domain', default='baseball', help='')
        parser.add_argument('-max_doc', default=20, type=int, help='')
        parser.add_argument('-max_core', default=24, type=int, help='')
        parser.add_argument('-timeout', default=320, type=int, help='')
        parser.add_argument('-join', default=320, type=int, help='')

        return parser.parse_args()

    def batch(self):
        """ """
        args = self.init_arguments()

        print(args.source_host, '->', args.target_host)
        print(args.source_index, '->', args.target_index)

        corpus_pipeline_url = 'http://172.20.78.250:20000/v1.0/batch'
        corpus_pipeline_url = 'http://localhost:20000/v1.0/batch'

        elastic_source = ElasticSearchUtils(host=args.source_host, http_auth=args.http_auth, index=args.source_index)
        elastic_target = ElasticSearchUtils(host=args.target_host, http_auth=args.http_auth, index=args.target_index)

        # crawler-naver-economy-2019 문서 목록 덤프
        source_query = {
            '_source': '',
            "query": {
                "range": {
                    "date": {
                        "gte": "2020-01-01T00:00:00",
                        "lte": "2020-04-20T00:00:00",
                    }
                }
            }
        }

        source_ids = elastic_source.get_id_list(index=args.source_index, query_cond=source_query)
        target_ids = elastic_target.get_id_list(index=args.target_index, query_cond=source_query)

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

        pool = Pool(processes=max_core)

        for i in trange(0, size, step, dynamic_ncols=True):
            st, en = (i, i + step - 1)
            if en > size:
                en = size + 1

            doc_list = []
            elastic_source.get_by_ids(
                index=args.source_index,
                source=None,
                result=doc_list,
                id_list=missing_ids[st:en],
            )

            # debug
            self.call_corpus_pipeline(
                doc_list,
                args.target_host,
                args.http_auth,
                args.target_index,
                corpus_pipeline_url,
                args.nlu_domain,
                args.timeout,
            )

            # pool.apply_async(
            #     self.call_corpus_pipeline,
            #     args=(
            #         doc_list,
            #         args.target_host,
            #         args.http_auth,
            #         args.target_index,
            #         corpus_pipeline_url,
            #         args.nlu_domain,
            #         args.timeout,
            #     )
            # )

            count += 1
            if count >= max_core:
                count = 0

                pool.close()
                pool.join()

                pool = Pool(processes=max_core)

        pool.close()
        pool.join()

        return


if __name__ == '__main__':
    utils = CorpusPipelineUtils()

    utils.batch()
