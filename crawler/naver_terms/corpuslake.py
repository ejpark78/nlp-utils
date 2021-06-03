#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import urllib3

from crawler.utils.es import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CorpusLake(object):
    """코퍼스 저장소"""

    def __init__(self, lake_info: dict):
        super().__init__()

        self.lake_info = lake_info
        self.lake_type = lake_info['type']

        self.es = None
        self.db = None

    def open(self) -> None:
        if self.lake_type == 'es':
            self.es = self.open_es()

        # if self.lake_type == 'sqlite':
        #     self.db = self.open_sqlite(**lake_info)

        return

    def open_es(self, lake_info: dict = None) -> ElasticSearchUtils:
        if lake_info is None:
            lake_info = self.lake_info

        return ElasticSearchUtils(
            host=lake_info['host'],
            index=lake_info['index'],
            bulk_size=lake_info['20'],
            http_auth=lake_info['auth'],
            mapping=lake_info['mapping']
        )

    def exists(self, **doc_info) -> bool:
        if self.lake_type == 'es':
            return self.es.conn.exists(index=doc_info['index'], id=doc_info['id'])

        return False

    def is_done(self, **doc_info) -> bool:
        """상세 페이지가 크롤링 결과에 있는지 확인한다. 만약 있다면 목록 인덱스에서 완료(*_done)으로 이동한다."""
        exists_doc = self.es.conn.exists(id=doc_info['doc_id'], index=doc_info['index'])

        if exists_doc is True:
            self.es.move_document(
                source_index=doc_info['list_index'],
                target_index=doc_info['done_index'],
                source_id=doc_info['list_id'],
                document_id=doc_info['doc_id'],
                merge_column=doc_info['merge_column'],
            )
            return True

        return False

    def set_done(self, **param) -> None:
        if self.lake_type == 'es':
            self.es.move_document(**param)
        return

    def merge(self, doc: dict, **doc_info) -> dict:
        if self.lake_type == 'es':
            return self.es.merge_doc(index=doc_info['index'], doc=doc, column=doc_info['column'])

        return doc

    def save(self, doc: dict, **doc_info) -> None:
        if self.lake_type == 'es':
            self.es.save_document(document=doc, **doc_info)

        return

    def flush(self) -> None:
        if self.lake_type == 'es':
            self.flush()

        return

    def dump(self, **params) -> list:
        if self.lake_type == 'es':
            result = []
            self.es.dump_index(index=params['index'], limit=params['limit'], size=params['limit'] + 1)
            return result

        return []
