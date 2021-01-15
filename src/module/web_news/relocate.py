#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

from nlplab.utils.elasticsearch_utils import ElasticSearchUtils
from tqdm import tqdm

from module.web_news.cache_utils import CacheUtils


class RelocateWebNews(object):

    def __init__(self):
        super().__init__()

        self.params = None

    @staticmethod
    def get_index(alias_info: dict, category: str) -> str or None:
        for col in alias_info.keys():
            if category.find(col) != 0:
                continue

            return alias_info[col]

        return None

    @staticmethod
    def parse_json(document: dict) -> dict:
        for col in document.keys():
            value = document[col]
            if isinstance(value, str) is False:
                continue

            if value == '':
                continue

            if value[-1] != ']' and value[-1] != '}':
                continue

            try:
                document[col] = json.loads(value)
                print(col)
            except ValueError:
                pass

        return document

    @staticmethod
    def remove_docs(doc_list: list, elastic: ElasticSearchUtils) -> None:
        bulk = []
        for doc in doc_list:
            # False 라면 source -> target 으로 이동후 삭제
            if doc['_target']['exists'] is False:
                #     bulk += [
                #         {
                #             'update': {
                #                 '_id': doc['_id'],
                #                 '_index': doc['_target']['_index'],
                #             }
                #         },
                #         {
                #             'doc': self.parse_json(document=doc['_source']),
                #             'doc_as_upsert': True,
                #         }
                #     ]
                continue

            # target_exists 가 True 라면 source 에서 삭제
            bulk += [
                {
                    'delete': {
                        '_id': doc['_id'],
                        '_index': doc['_source']['_index'],
                    }
                }
            ]

        if len(bulk) > 0:
            elastic.conn.bulk(
                index=bulk[-1]['delete']['_index'],
                body=bulk,
                refresh=True,
                params={'request_timeout': 620},
            )

        return

    def relocate(self) -> None:
        elastic = ElasticSearchUtils(host=self.params.host, http_auth=self.params.auth)

        alias_info = {
            'IT': 'crawler-naver-it-2020',
            'TV': 'crawler-naver-tv-2020',
            '경제': 'crawler-naver-economy-2020',
            '사회': 'crawler-naver-society-2020',
            '생활': 'crawler-naver-living-2020',
            '세계': 'crawler-naver-international-2020',
            '스포츠': 'crawler-naver-sports-2020',
            '오피니언': 'crawler-naver-opinion-2020',
            '정치': 'crawler-naver-politics-2020',
        }

        # df = pd.read_sql_query('SELECT _id,_index,date,category,content FROM documents WHERE content=""', con)
        # pd.set_option('display.max_rows', None)
        # df.groupby(by='category').size().to_frame()
        # exists = self.is_exists(df=df, index_info=index_info, elastic=elastic)

        tbl = 'documents'
        size = 500
        where = 'WHERE content=""'

        filename = 'data/news/naver-relocate/crawler-naver-economy-2020.db'
        filename = 'data/news/naver-relocate/crawler-naver-international-2020.db'
        filename = 'data/news/naver-relocate/crawler-naver-it-2020.db'
        # filename = 'data/news/naver-relocate/crawler-naver-tv-2020.db'
        filename = 'data/news/naver-relocate/crawler-naver-society-2020.db'
        filename = 'data/news/naver-relocate/crawler-naver-living-2020.db'
        filename = 'data/news/naver-relocate/crawler-naver-sports-2020.db'
        filename = 'data/news/naver-relocate/crawler-naver-opinion-2020.db'
        filename = 'data/news/naver-relocate/crawler-naver-politics-2020.db'

        db = CacheUtils(filename=filename)

        p_bar = tqdm(
            desc=filename.split('/')[-1],
            total=db.table_size(tbl=tbl, where=where),
            unit_scale=True,
            dynamic_ncols=True
        )

        db.cursor.execute('SELECT * FROM {tbl} {where}'.format(tbl=tbl, where=where))
        rows = db.cursor.fetchmany(size)

        db_cols = [d[0] for d in db.cursor.description]

        while rows:
            docs = []
            doc_index = {}
            for values in rows:
                doc = dict(zip(db_cols, values))

                doc_index[doc['_id']] = doc

                index = self.get_index(alias_info=alias_info, category=doc['category'])
                if index is None:
                    p_bar.update(1)
                    continue

                docs.append({
                    '_id': doc['_id'],
                    '_index': index,
                })

                p_bar.update(1)

            resp = elastic.conn.mget(
                body={
                    'docs': docs
                },
                _source=['category'],
            )

            doc_list = []
            for x in resp['docs']:
                source = doc_index[x['_id']]

                if source['_index'] == x['_index']:
                    continue

                doc_list.append({
                    '_id': x['_id'],
                    '_source': source,
                    '_target': {
                        '_index': x['_index'],
                        'exists': x['found'],
                        'category': x['_source']['category'] if '_source' in x else '',
                    }
                })

            # target_exists 가 True 라면 source 에서 삭제
            # False 라면 source -> target 으로 이동후 삭제
            self.remove_docs(doc_list=doc_list, elastic=elastic)

            rows = db.cursor.fetchmany(size)

        return

    def batch(self) -> None:
        self.params = self.init_arguments()

        if self.params.dump_index is True:
            elastic = ElasticSearchUtils(host=self.params.host, http_auth=self.params.auth)
            elastic.dump_index(index=self.params.index, size=self.params.size)

        if self.params.json2db is True:
            CacheUtils().json2db(filename=self.params.filename)

        if self.params.relocate is True:
            self.relocate()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--dump-index', action='store_true', default=False)
        parser.add_argument('--relocate', action='store_true', default=False)
        parser.add_argument('--json2db', action='store_true', default=False)

        parser.add_argument('--host', default='https://corpus.ncsoft.com:9200', help='elasticsearch url')
        parser.add_argument('--auth', default='elastic:nlplab', help='elasticsearch auth')

        parser.add_argument('--filename', default=None, help='json file name')
        parser.add_argument('--index', default=None, help='elasticsearch index name')
        parser.add_argument('--size', default=1000, type=int, help='bulk size')

        return parser.parse_args()


if __name__ == '__main__':
    RelocateWebNews().batch()
