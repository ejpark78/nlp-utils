#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
from os import makedirs, getenv
from os.path import dirname, isdir

import urllib3
from elasticsearch import Elasticsearch
from nlplab.utils.logger import Logger
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class ElasticSearchUtils(object):

    def __init__(self, host: str = None, http_auth: str = None):
        self.host = host
        if host is None:
            self.host = getenv('NLPLAB_ES_HOST', 'https://corpus.ncsoft.com:9200')

        if http_auth is None:
            http_auth = getenv('NLPLAB_ES_AUTH', 'elastic:nlplab')

        self.http_auth = (http_auth.split(':'))

        self.logger = Logger()
        self.conn = None

        if self.host is not None:
            self.open()

    def open(self) -> None:
        try:
            self.conn = Elasticsearch(
                hosts=self.host,
                timeout=60,
                http_auth=self.http_auth,
                use_ssl=False,
                verify_certs=False,
                ssl_show_warn=False
            )
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '서버 접속 에러',
                'index': self.host,
                'e': str(e),
            })
            return

        return

    def index_list(self):
        return [v for v in self.conn.indices.get('*') if v[0] != '.']

    def scroll(self, index: str, scroll_id: str, size: int = 1000, source: list = None) -> dict:
        params = {
            'request_timeout': 10 * 60
        }

        # 스크롤 아이디가 있다면 scroll 함수 호출
        if scroll_id == '':
            search_result = self.conn.search(
                index=index,
                scroll='2m',
                size=size,
                params=params,
                _source=source,
            )
        else:
            search_result = self.conn.scroll(
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

        return {
            'hits': hits['hits'],
            'total': total,
            'scroll_id': scroll_id,
        }

    def export(self, index: str, filename: str, source: list = None) -> None:
        path = dirname(filename)
        if isdir(path) is False:
            makedirs(path)

        count = 1
        size = 1000
        sum_count = 0
        scroll_id = ''

        p_bar = None
        with bz2.open(filename=filename, mode='wb') as fp:
            while count > 0:
                resp = self.scroll(index=index, size=size, scroll_id=scroll_id, source=source)

                count = len(resp['hits'])
                scroll_id = resp['scroll_id']

                if p_bar is None:
                    p_bar = tqdm(
                        desc='downloading: {}'.format(index),
                        total=resp['total'],
                        dynamic_ncols=True
                    )

                p_bar.update(count)
                sum_count += count

                for item in resp['hits']:
                    doc = item['_source']

                    doc['_id'] = item['_id']
                    doc['_index'] = item['_index']
                    if 'document_id' in item:
                        del item['document_id']

                    line = json.dumps(doc, ensure_ascii=False, sort_keys=True) + '\n'
                    fp.write(line.encode('utf-8'))

        if p_bar is not None:
            p_bar.close()

        return

    @staticmethod
    def change_case(text: str) -> str:
        return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', text)).lower()

    def get_properties(self, mappings: dict) -> dict:
        props = mappings['properties']
        return {self.change_case(col): props[col]['type'] if 'type' in props[col] else 'json' for col in props}

    def dump_index(self, index: str, size: int = 1000) -> None:
        if index is None or index == '':
            return

        count = 1
        sum_count = 0
        scroll_id = ''

        # save settings/mapping
        settings = {
            **self.conn.indices.get_settings(index)[index],
            **self.conn.indices.get_mapping(index)[index]
        }

        print(json.dumps(settings, ensure_ascii=False), flush=True)

        p_bar = None
        while count > 0:
            resp = self.scroll(index=index, size=size, scroll_id=scroll_id)

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
            sum_count += count

            for item in resp['hits']:
                doc = item['_source']

                doc.update({
                    '_id': item['_id'],
                    '_index': item['_index'],
                })

                print(json.dumps(doc, ensure_ascii=False), flush=True)

        return
