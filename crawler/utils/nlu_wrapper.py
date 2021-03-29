#!./venv/bin/python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from collections import defaultdict

import pytz
import requests
import urllib3

from crawler.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


class NLUWrapper(object):

    def __init__(self):
        self.host = None
        self.auth = None
        self.timeout = 120

        self.options = {
            'domain': 'economy',
            'style': 'literary',
            'module': [
                'SBD_crf',
                'POS',
                'NER'
            ]
        }

        self.logger = Logger()
        self.timezone = pytz.timezone('Asia/Seoul')

    def open(self, host: str, auth: str = None, timeout: int = 120) -> None:
        self.host = host
        self.auth = auth
        self.timeout = timeout
        return

    @staticmethod
    def simplify(doc_list: list) -> list:
        dep_columns = 'index,head,morp,pos,func'.split(',')
        result_columns = set('text,morp_str,ne_str'.split(','))

        result, sent_id, doc_id = [], 1, ''
        for doc in doc_list:
            meta = doc['meta'] if 'meta' in doc else {}
            if '_id' in meta and doc_id != meta['_id']:
                doc_id = meta['_id']
                sent_id = 1

            for sent in doc['sentences']:
                item = defaultdict(str)

                # 결과 변환: 시간 필드 변경
                if 'time_results' in item:
                    if len(sent['time_results']) > 0:
                        item['times_str'] = json.dumps(sent['time_results'], ensure_ascii=False)

                # depen_str 변환
                if 'depen_str' in item and len(sent['depen_str']) > 0:
                    depen = [dict(zip(dep_columns, dep)) for dep in sent['depen_str']]
                    item['depen_str'] = json.dumps(depen, ensure_ascii=False)

                for k in result_columns:
                    if k not in sent:
                        continue

                    item[k] = sent[k]

                result.append({'sentence_id': sent_id, **meta, **item})
                sent_id += 1

        return result

    @staticmethod
    def make_doc(text: str, modules: set, meta: dict) -> list:
        text_list = [text]
        if isinstance(text, list):
            text_list = text

        # POST 메세지
        if 'SBD' in modules or 'SBD_crf' in modules:
            return [{
                'meta': meta,
                'contents': x.replace(r'\xa0', ' ').replace(r'\n', ' '),
            } for x in text_list]

        return [{
            'sentences': [{
                'meta': meta,
                'text': x,
            }]
        } for x in text_list]

    def request(self, doc_list: list, options: dict, domain: str, style: str) -> list:
        if len(doc_list) == 0:
            return []

        options['domain'] = domain
        options['style'] = style

        try:
            resp = requests.post(
                url=self.host,
                json={
                    'nlu_wrapper': {
                        'option': options
                    },
                    'doc': doc_list
                },
                timeout=self.timeout,
                verify=False
            )
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'NLU Wrapper 호출 에러',
                'host': self.host,
                'exception': str(e),
            })

            return []

        # Internal Server Error 처리
        if resp.status_code // 100 == 5:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'NLU Wrapper 서버 에러',
                'doc_list': list(set([f"{x['meta']['_index']}/{x['meta']['_id']}" for x in doc_list if 'meta' in x])),
                'resp': resp.text,
            })

            return []

        # 결과 취합
        try:
            resp_data = resp.json()
            return self.simplify(doc_list=resp_data['doc'])
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'NLU Wrapper 결과 취합 에러',
                'doc_list': list(set([f"{x['meta']['_index']}/{x['meta']['_id']}" for x in doc_list if 'meta' in x])),
                'exception': str(e),
            })

        return []


if __name__ == '__main__':
    pass
