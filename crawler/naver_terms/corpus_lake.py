#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import urllib3

from crawler.naver_terms.cache import Cache
from crawler.utils.es import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CorpusLake(object):
    """코퍼스 저장소"""

    def __init__(self, lake_info: dict):
        super().__init__()

        self.lake_info = lake_info
        self.lake_type = set(lake_info['type'].split(','))

        self.es = None
        self.db = None

        self.open()

    def open(self) -> None:
        if 'sqlite' in self.lake_type:
            self.db = Cache(filename=self.lake_info['filename'], tbl=self.lake_info['index'])

        if 'elasticsearch' in self.lake_type:
            self.es = self.open_es()

        return

    def open_es(self, lake_info: dict = None) -> ElasticSearchUtils:
        if lake_info is None:
            lake_info = self.lake_info

        return ElasticSearchUtils(
            host=lake_info['host'],
            index=lake_info['index'],
            bulk_size=lake_info['bulk_size'],
            http_auth=lake_info['auth'],
            mapping=lake_info['mapping']
        )

    def exists(self, **doc_info) -> bool:
        if 'sqlite' in self.lake_type:
            return self.db.table_exits(tbl=doc_info['index'])

        if 'elasticsearch' in self.lake_type:
            return self.es.conn.exists(index=doc_info['index'], id=doc_info['id'])

        return False

    def set_done(self, index: str, doc_id: str) -> None:
        if 'sqlite' in self.lake_type:
            self.db.set_done(tbl=index, doc_id=doc_id)

        if 'elasticsearch' in self.lake_type:
            self.es.conn.update(
                index=index,
                id=doc_id,
                body={
                    'doc': {
                        'done': 1,
                    }
                },
                refresh=True,
            )

        return

    def merge(self, doc: dict, **doc_info) -> dict:
        if 'sqlite' in self.lake_type:
            pass

        if 'elasticsearch' in self.lake_type:
            return self.es.merge_doc(index=doc_info['index'], doc=doc, column=doc_info['column'])

        return doc

    def save(self, doc: dict, doc_id: str, index: str) -> None:
        if 'sqlite' in self.lake_type:
            self.db.save_doc(tbl=index, doc=doc, doc_id=doc_id)

        if 'elasticsearch' in self.lake_type:
            self.es.save_document(document=doc, index=index)

        return

    def flush(self) -> None:
        if 'sqlite' in self.lake_type:
            self.db.conn.commit()

        if 'elasticsearch' in self.lake_type:
            self.es.flush()

        return

    def dump(self, **params) -> list:
        if 'sqlite' in self.lake_type:
            return self.db.dump(tbl=params['index'], size=params['limit'])

        if 'elasticsearch' in self.lake_type:
            result = []
            self.es.dump_index(
                index=params['index'],
                limit=params['limit'],
                query=params['query'],
                size=params['limit'] + 1
            )
            return result

        return []

    def dump_index(self, index: str, fp) -> None:
        if 'sqlite' in self.lake_type:
            self.db.dump_table(tbl=index, fp=fp)

        if 'elasticsearch' in self.lake_type:
            pass

        return
