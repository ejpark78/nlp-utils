#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import ssl
from datetime import datetime, timezone, timedelta
from os.path import isfile

import pytz
import urllib3
from dateutil.parser import parse as parse_date
from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context

from logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


MESSAGE = 25
logger = logging.getLogger()

bulk_data = []


class ElasticSearchUtils(object):
    """후처리"""

    def __init__(self):
        """생성자"""
        self.elastic = {}

        self.timezone = pytz.timezone('Asia/Seoul')
        self.kst_timezone = timezone(timedelta(hours=9))

    def open(self, host, index, http_auth):
        """elastic-search 연결"""
        if host in self.elastic:
            return self.elastic[host]

        msg = {
            'level': 'INFO',
            'message': '서버 연결',
            'host': host,
        }
        logger.info(msg=LogMsg(msg))

        # https://github.com/elastic/elasticsearch-py/issues/712
        ssl_context = create_ssl_context()

        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # host 접속
        try:
            self.elastic[host] = Elasticsearch(
                hosts=host.split(','),
                http_auth=(http_auth.split(':')),
                timeout=30,
                ssl_context=ssl_context,
                verify_certs=False,
                ssl_show_warn=False,
            )
        except Exception as e:
            log_msg = {
                'level': 'ERROR',
                'message': '서버 접속 에러',
                'host': host,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(log_msg))
            return

        return self.elastic[host]

    @staticmethod
    def create_index(elastic, index_name=None):
        """인덱스 생성"""
        if elastic is None:
            return

        mapping = {}
        filename = 'utils/mapping.json'
        if isfile(filename):
            with open(filename, 'rt') as fp:
                mapping = json.loads(''.join(fp.readlines()))

        try:
            elastic.indices.create(
                body=mapping,
                index=index_name,
            )

            msg = {
                'level': 'MESSAGE',
                'message': '인덱스 생성',
                'index': index_name,
                'mapping': mapping,
            }
            logger.log(level=MESSAGE, msg=LogMsg(msg))
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '인덱스 생성 오류',
                'index': index_name,
                'mapping': mapping,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        return

    def convert_date(self, document):
        """날짜 형식을 elastic search 에서 검색할 수 있도록 변경"""

        def _convert(_doc):
            # 날짜 변환
            if 'date' in _doc:
                if isinstance(_doc['date'], str):
                    dt = parse_date(_doc['date'])
                    _doc['date'] = dt.replace(tzinfo=self.kst_timezone)

                _doc['date'] = _doc['date'].isoformat()

            # 입력시간 삽입
            if 'insert_date' not in _doc:
                _doc['insert_date'] = datetime.now(self.timezone).isoformat()

            return _doc

        if isinstance(document, list):
            for i in range(len(document)):
                document[i] = _convert(document[i])
        elif isinstance(document, dict):
            document = _convert(document)

        return document

    def get_index_year_tag(self, date):
        """인덱스의 년도 태그를 반환한다."""
        from dateutil.parser import parse as parse_date

        if isinstance(date, str):
            date = parse_date(date)
            if date.tzinfo is None:
                date = self.timezone.localize(date)
        return date.year

    @staticmethod
    def get_target_index(index, split_index=False, tag=None):
        """복사 대상의 인덱스를 반환한다."""
        if split_index is False or tag is None:
            return index

        # 인덱스에서 crawler-naver-sports-2018 연도를 삭제한다.
        token = index.rsplit('-', maxsplit=1)
        if len(token) == 2 and token[-1].isdecimal() is True:
            index = token[0]

        return '{index}-{tag}'.format(index=index, tag=tag)

    def save_document(self, document, elastic_info):
        """전처리 결과를 elastic search 에 저장"""
        global bulk_data

        if isinstance(document, list):
            doc_list = document
        else:
            doc_list = [document]

        # 저장
        for doc in doc_list:
            # 인덱스명 추출
            index = elastic_info['index']
            if 'split_index' in elastic_info and elastic_info['split_index'] is True and 'date' in doc:
                index = self.get_target_index(
                    tag=self.get_index_year_tag(date=doc['date']),
                    index=elastic_info['index'],
                    split_index=elastic_info['split_index'],
                )

            # 날짜 변환
            doc = self.convert_date(document=doc)

            # id 제거
            if '_id' in doc:
                doc['document_id'] = doc['_id']
                del doc['_id']

            # 삭제
            bulk_data.append({
                'delete': {
                    '_index': index,
                    '_id': doc['document_id'],
                }
            })

            # 저장 정보
            bulk_data.append({
                'update': {
                    '_index': index,
                    '_id': doc['document_id'],
                }
            })

            for k in ['_index', '_type']:
                if k in doc:
                    del doc[k]

            # 저장 문서
            bulk_data.append({
                'doc': doc,
                'doc_as_upsert': True
            })

            # 문서 정보 추출
            doc_info = {}
            for k in ['title', 'date']:
                if k not in doc:
                    continue

                doc_info[k] = doc[k]

            # 로그 메세지 생성
            log_msg = {
                'level': 'MESSAGE',
                'message': '문서 저장 성공',
                'doc_url': '{host}/{index}/_doc/{doc_id}?pretty'.format(
                    host=elastic_info['host'],
                    index=index,
                    doc_id=doc['document_id'],
                ),
            }
            log_msg.update(doc_info)

            # 문서 저장
            self.flush(elastic_info=elastic_info, log_msg=log_msg)
            bulk_data = []

        return

    def flush(self, elastic_info, log_msg):
        """문서를 저장한다."""
        global bulk_data

        if len(bulk_data) == 0:
            return {}

        elastic = self.open(
            host=elastic_info['host'],
            index=elastic_info['index'],
            http_auth=elastic_info['http_auth'],
        )

        # 문서 저장
        try:
            response = elastic.bulk(body=bulk_data, refresh=True)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '문서 저장 오류',
                'host': elastic_info['host'],
                'index': elastic_info['index'],
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))
            return {}

        if response['errors'] is False:
            logger.log(level=MESSAGE, msg=LogMsg(log_msg))
            return response

        # 저장 로그 생성
        try:
            reason = []
            for item in response['items']:
                if 'update' not in item:
                    continue

                txt = item['update']['error']['reason']
                if txt.strip() == '':
                    continue

                reason.append(txt)

            msg = {
                'level': 'ERROR',
                'message': '문서 저장 에러',
                'host': elastic_info['host'],
                'index': elastic_info['index'],
                'reason': reason,
            }

            if len(reason) == 0:
                msg['response'] = response

            logger.error(msg=LogMsg(msg))
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '로깅 에러',
                'host': elastic_info['host'],
                'index': elastic_info['index'],
                'response': response,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        return response
