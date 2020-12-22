#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from elasticsearch import Elasticsearch
from tqdm import tqdm


class SyncElasticsearchIndex(object):

    def __init__(self):
        super().__init__()

    @staticmethod
    def open_es(host: str, http_auth: str) -> Elasticsearch:
        return Elasticsearch(
            hosts=host,
            timeout=60,
            http_auth=http_auth,
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False
        )

    @staticmethod
    def scroll(es: Elasticsearch, index: str, scroll_id: str, size: int = 1000) -> dict:
        params = {
            'request_timeout': 620
        }

        # 스크롤 아이디가 있다면 scroll 함수 호출
        if scroll_id == '':
            search_result = es.search(
                index=index,
                scroll='2m',
                size=size,
                params=params,
            )
        else:
            search_result = es.scroll(
                scroll_id=scroll_id,
                scroll='2m',
                params=params,
            )

        # 검색 결과 추출
        hits = search_result['hits']
        scroll_id = search_result['_scroll_id']

        total = hits['total']
        if isinstance(total, dict) and 'value' in total:
            total = total['value']

        return {
            'hits': hits['hits'],
            'total': total,
            'scroll_id': scroll_id,
        }

    def sync_index(self, src_es: Elasticsearch, trg_es: Elasticsearch, index: str, size: int = 500) -> None:
        count = 1
        scroll_id = ''

        p_bar = None
        while count > 0:
            resp = self.scroll(es=src_es, index=index, size=size, scroll_id=scroll_id)

            count = len(resp['hits'])
            scroll_id = resp['scroll_id']

            if p_bar is None:
                p_bar = tqdm(
                    desc=index,
                    total=resp['total'],
                    unit_scale=True,
                    dynamic_ncols=True
                )

            p_bar.update(count)

            bulk = []
            for item in resp['hits']:
                bulk += [
                    {
                        'delete': {
                            '_id': item['_id'],
                            '_index': item['_index'],
                        }
                    },
                    {
                        'update': {
                            '_id': item['_id'],
                            '_index': item['_index'],
                        }
                    },
                    {
                        'doc': item['_source'],
                        'doc_as_upsert': True,
                    }
                ]

            if len(bulk) == 0:
                continue

            _ = trg_es.bulk(
                index=index,
                body=bulk,
                refresh=True,
                params={'request_timeout': 620},
            )

        return

    def batch(self) -> None:
        params = self.init_arguments()

        src_es = self.open_es(host=params.src_host, http_auth=params.src_auth)
        trg_es = self.open_es(host=params.trg_host, http_auth=params.trg_auth)

        index_list = [params.index]
        if params.index is None:
            index_list = [v for v in src_es.indices.get('*') if v[0] != '.']

        for index in index_list:
            self.sync_index(src_es=src_es, trg_es=trg_es, index=index)

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--index', default=None, help='인덱스명')
        parser.add_argument('--size', default=500, type=int, help='한번에 복사할 문서수')

        parser.add_argument('--src-host', default='https://dmz:8200', help='source host')
        parser.add_argument('--src-auth', default='elastic:nlplab', help='source http auth')

        parser.add_argument('--trg-host', default='http://localhost:9200', help='target host')
        parser.add_argument('--trg-auth', default='elastic:nlplab', help='target http auth')

        return parser.parse_args()


if __name__ == '__main__':
    SyncElasticsearchIndex().batch()
