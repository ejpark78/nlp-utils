#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import defaultdict
from datetime import datetime
from os import getenv
from time import sleep

import pytz
import yaml
from dateutil.parser import parse as parse_date
from tqdm import tqdm

from crawler.utils.elasticsearch import ElasticSearchUtils
from crawler.utils.html_parser import HtmlParser
from crawler.utils.logger import Logger
from crawler.utils.mysql import MysqlUtils
from crawler.utils.nlu_wrapper import NLUWrapper


class Pipeline(object):
    """ETL Pipeline"""

    def __init__(self):
        self.params = None

        self.logger = Logger()

        self.parser = HtmlParser()
        self.result_db = MysqlUtils()
        self.nlu_wrapper = NLUWrapper()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.source = 'url,title,date,paper,source,category,content,contents,raw,raw_list'.split(',')

        self.es = None

        # summary
        self.summary = defaultdict(int)
        self.start_date = datetime.now(self.timezone)

    @staticmethod
    def open_config(filename: str) -> list:
        file_list = filename.split(',')

        result = []
        for f_name in file_list:
            with open(f_name, 'r') as fp:
                data = yaml.load(stream=fp, Loader=yaml.FullLoader)
                result.append(dict(data))

        return result

    def masking_auth(self, obj: dict) -> None:
        for k, v in obj.items():
            if isinstance(v, dict):
                self.masking_auth(obj=v)
            elif k.find('auth') >= 0:
                obj[k] = '*****'

        return

    def show_summary(self, tag: str = '') -> None:
        finished = datetime.now(self.timezone)
        runtime = finished - self.start_date

        summary = {
            'tag': tag,
            'start': self.start_date.isoformat(),
            'runtime': f'{runtime.total_seconds():0.2f}',
            'finished': finished.isoformat(),
            'params': {
                **self.params
            },
            **self.summary,
        }
        self.masking_auth(obj=summary)

        self.logger.log(msg={'level': 'SUMMARY', **summary})

        ElasticSearchUtils(
            host=self.params['host'],
            http_auth=self.params['auth']
        ).save_summary(
            index='crawler-summary',
            summary=summary
        )
        return

    def make_request(self, document: dict, modules: set) -> list:
        """하나의 문서를 코퍼스 전처리 한다.

        document = {
            "_id": "015-0004155554",
            "title": "LG화학 등 2차전지株 '재충전'…파트론 등 휴대폰 부품株도 주목",
            "paper": "0면",
            "category": "경제/증권",
            "content": "美 금리 인하 기대 커지는데…수혜주는 어디\\n美 통화정책 완화 현실화되면...",
            "date": "2019-06-09T16:13:00+09:00"
        }
        """
        meta_columns = set('_index,_id,paper,date,source,category'.split(','))

        para_id, result = 1, []

        # 제목 처리
        if 'title' in document and document['title'] != '':
            result += self.nlu_wrapper.make_doc(
                meta={
                    'paragraph_id': para_id,
                    'position': 'title',
                    **{x: document[x] for x in meta_columns if x in document}
                },
                text=document['title'],
                modules=modules,
            )

        para_id += 1

        # 이미지 자막 처리
        if 'image_list' in document:
            for item in document['image_list']:
                if 'caption' not in item or item['caption'] == '':
                    continue

                text_list = [item['caption']]
                if isinstance(item['caption'], list):
                    text_list = item['caption']

                for text in [x for x in text_list if x != '']:
                    result += self.nlu_wrapper.make_doc(
                        meta={
                            'paragraph_id': para_id,
                            'position': 'caption',
                            **{x: document[x] for x in meta_columns if x in document}
                        },
                        text=text,
                        modules=modules,
                    )

            para_id += 1

        # 기사 본문 처리
        if 'content' in document and 'contents' not in document:
            document['contents'] = document['content']
            del document['content']

        if 'contents' in document:
            for text in document['contents'].split('\n'):
                text = text.strip()
                if text == '':
                    continue

                result += self.nlu_wrapper.make_doc(
                    meta={
                        'paragraph_id': para_id,
                        'position': 'contents',
                        **{x: document[x] for x in meta_columns if x in document}
                    },
                    text=text,
                    modules=modules,
                )

            para_id += 1

        return result

    def get_doc_list(self, doc_ids: set) -> list:
        query = {
            '_source': '',
            'track_total_hits': True,
            **self.es.get_date_range_query(
                date_range=self.params['date_range'],
                date_column='date'
            )
        }

        doc_id_list = self.es.get_id_list(index=self.params['index'], limit=self.params['limit'], query=query)

        result = [x for x in doc_id_list if tuple([x['_index'], x['_id']]) not in doc_ids]

        self.summary['skip_docs'] += len(doc_id_list) - len(result)
        self.summary['search_docs'] += len(doc_id_list)

        return result

    def analyze(self, doc_list: list, bulk_size: int = 50) -> list:
        if len(doc_list) == 0:
            return []

        style, domain = 'literary', 'economy'
        bulk, doc_buf, error_docs = [], [], []

        options = {**self.nlu_wrapper.options}

        for doc in tqdm(doc_list, desc='NLU Wrapper'):
            bulk += self.make_request(
                document=doc,
                modules=set(self.nlu_wrapper.options['module'])
            )
            doc_buf.append(doc)

            if len(bulk) > bulk_size:
                resp = self.nlu_wrapper.request(doc_list=bulk, style=style, domain=domain, options=options)
                self.result_db.save_result(doc_list=resp, verbose=self.params['verbose'])

                if len(resp) == 0:
                    error_docs += doc_buf
                else:
                    self.summary['nlu_docs'] += len(resp)

                bulk, doc_buf = [], []
                sleep(self.params['sleep'])

        if len(bulk) == 0:
            return error_docs

        resp = self.nlu_wrapper.request(doc_list=bulk, style=style, domain=domain, options=options)
        self.result_db.save_result(doc_list=resp, verbose=self.params['verbose'])

        if len(resp) == 0:
            error_docs += doc_buf
        else:
            self.summary['nlu_docs'] += len(resp)

        return error_docs

    def pipeline(self, doc_id_list: list, config: dict, index: str, name: str = 'common') -> None:
        task_list = defaultdict(list)
        for x in config['pipeline'][name]:
            task_list[x['column']].append(x)

        start, end, size = 0, self.params['bulk_size'], self.params['bulk_size']

        while start < len(doc_id_list):
            doc_list = []
            self.es.get_by_ids(
                id_list=[x['_id'] for x in doc_id_list[start:end]],
                index=index,
                source=self.source,
                result=doc_list
            )

            if start >= len(doc_id_list):
                break

            start, end = end, end + size
            if end > len(doc_id_list):
                end = len(doc_id_list)

            for doc in tqdm(doc_list, desc='Pipeline'):
                for col, tasks in task_list.items():
                    if col not in doc:
                        continue

                    soup = self.parser.parse_html(
                        html=doc[col],
                        parser_type=config['parsing']['parser'],
                    )

                    parser_version = config['parsing']['version'] if 'version' in config['parsing'] else None

                    item = self.parser.parse(
                        html=None,
                        soup=soup,
                        base_url=doc['url'],
                        parsing_info=tasks,
                        default_date=parse_date(doc['date']),
                        parser_version=parser_version,
                    )
                    doc.update(item)

            # analyze
            error_docs = self.analyze(doc_list=doc_list, bulk_size=self.params['bulk_size'])
            self.summary['error_docs'] += len(error_docs)

            error_docs = self.analyze(doc_list=error_docs, bulk_size=self.params['bulk_size'] // 2)
            self.summary['retry_error_docs'] += len(error_docs)

            error_docs = self.analyze(doc_list=error_docs, bulk_size=1)
            self.summary['retry_error_docs'] += len(error_docs)

        return None

    def batch(self) -> None:
        """
        1. es date range dump
        2. apply config pipeline: parse raw
        3. call nlu wrapper
        4. save result
        5. summary
        """
        self.params = self.init_arguments()

        config_list = self.open_config(filename=self.params['config'])

        self.nlu_wrapper.open(
            host=self.params['nlu_wrapper_host'],
            timeout=self.params['timeout']
        )

        self.result_db.open(
            host=self.params['result_host'],
            auth=self.params['result_auth'],
            database=self.params['result_database'],
            table_name=self.params['result_table_name']
        )

        doc_ids = self.result_db.get_ids(date_range=self.params['date_range'], table_name='naver_idx')

        # dump article
        self.es = ElasticSearchUtils(host=self.params['host'], http_auth=self.params['auth'])

        doc_id_list = self.get_doc_list(doc_ids=doc_ids)

        idx_grp = defaultdict(list)
        for x in doc_id_list:
            idx_grp[x['_index']].append(x)

        # pipeline
        for idx, ids in idx_grp.items():
            self.pipeline(doc_id_list=ids, config=config_list[0], index=idx)

        # update index table
        self.result_db.update_idx(index_table='naver_idx', source_table='naver', date_range=self.params['date_range'])

        # summary
        self.show_summary()

        self.result_db.close()

        return

    @staticmethod
    def init_arguments() -> dict:
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('--host', type=str, help='elasticsearch url',
                            default=getenv('ELASTIC_SEARCH_HOST', default=None))
        parser.add_argument('--auth', type=str, help='elasticsearch auth',
                            default=getenv('ELASTIC_SEARCH_AUTH', default=None))

        parser.add_argument('--index', help='인덱스명',
                            default=getenv('ELASTIC_INDEX', default='crawler-naver-*-2021'))

        parser.add_argument('--result-host', default=getenv('DB_HOST', default='crawler-mysql.cloud.ncsoft.com'))
        parser.add_argument('--result-auth', default=getenv('DB_AUTH', default='root:searchT2020'))
        parser.add_argument('--result-database', default=getenv('DB_DATABASE', default='naver'))
        parser.add_argument('--result-table-name', default=getenv('DB_TABLE', default='naver'))

        parser.add_argument('--nlu-wrapper-host', default=getenv('NLU_WRAPPER_HOST', default='http://172.20.40.142'))
        # parser.add_argument('--nlu-wrapper-host', default='http://172.20.92.249:32001', help='통합망 서버')

        parser.add_argument('--limit', default=-1, type=int, help='한번에 분석하는 수량')
        parser.add_argument('--bulk-size', default=50, type=int, help='NLU Wrapper 호출 수량')
        parser.add_argument('--timeout', default=60, type=int, help='NLU Wrapper 호출 timeout')
        parser.add_argument('--sleep', default=1, type=float, help='호출 간격')

        parser.add_argument('--date-range', default=None, type=str, help='date 날짜 범위: 2000-01-01~2019-04-10')

        # flow-control
        parser.add_argument('--pipeline', default='', type=str, help='TODO: pipeline')

        # essential
        parser.add_argument('--config', default=None, type=str, help='설정 파일 정보')

        parser.add_argument('--verbose', default=-1, type=int, help='(optional) verbose 모드')

        return vars(parser.parse_args())


if __name__ == '__main__':
    Pipeline().batch()
