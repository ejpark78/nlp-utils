#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import pickle
import ssl
from datetime import datetime
from os import makedirs
from os.path import isfile, isdir

import pytz
import urllib3
from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context
from tqdm.autonotebook import tqdm

from utils import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ElasticSearchUtils(object):
    """엘라스틱 서치"""

    def __init__(self, host, index, insert=True, http_auth='crawler:crawler2019', bulk_size=1000,
                 tag=None, split_index=False, log_path='log'):
        """ 생성자 """
        self.host = host
        self.http_auth = (http_auth.split(':'))

        self.elastic = None
        self.split_index = split_index

        self.index = self.get_target_index(
            tag=tag,
            index=index,
            split_index=split_index,
        )

        self.bulk_data = {}
        self.bulk_size = bulk_size

        self.insert = insert

        self.timezone = pytz.timezone('Asia/Seoul')

        self.log_path = log_path

        self.logger = Logger()

        self.params = {'request_timeout': 620}

        if self.host is not None:
            self.open()

    def create_index(self, elastic, index=None):
        """인덱스를 생성한다."""
        if elastic is None:
            return False

        try:
            elastic.indices.create(
                index=index,
                body={
                    'settings': {
                        'number_of_shards': 3,
                        'number_of_replicas': 3
                    },
                    # 'mapping.total_fields.limit': 900000
                }
            )
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '인덱스 생성 에러',
                'host': self.host,
                'index': self.index,
                'exception': str(e),
            })
            return

        return True

    def convert_datetime(self, document):
        """ 입력받은 문서에서 데이터 타입이 datetime 를 문자열로 변환한다."""
        if document is None:
            return None

        for k in document:
            item = document[k]

            if isinstance(item, datetime):
                document[k] = item.isoformat()

            if isinstance(item, dict):
                self.convert_datetime(document=item)

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
        if index is None:
            return None

        if split_index is False or tag is None:
            return index

        # 인덱스에서 crawler-naver-sports-2018 연도를 삭제한다.
        token = index.rsplit('-', maxsplit=1)
        if len(token) == 2 and token[-1].isdecimal() is True:
            index = token[0]

        return '{index}-{tag}'.format(index=index, tag=tag)

    @staticmethod
    def get_ssl_verify_mode():
        """ssl 모드 설정을 반환한다."""
        # https://github.com/elastic/elasticsearch-py/issues/712
        ssl_context = create_ssl_context()

        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        return ssl_context

    def open(self):
        """서버에 접속한다."""

        # host 접속
        try:
            self.elastic = Elasticsearch(
                hosts=self.host,
                timeout=self.params['request_timeout'],
                http_auth=self.http_auth,
                verify_certs=False,
                ssl_show_warn=False,
                ssl_context=self.get_ssl_verify_mode(),
                http_compress=True,
            )
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '서버 접속 에러',
                'host': self.host,
                'exception': str(e),
            })
            return

        if self.split_index is True:
            return

        # 인덱스가 없는 경우, 생성함
        try:
            if self.elastic.indices.exists(index=self.index) is False:
                self.create_index(self.elastic, self.index)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '인덱스 확인 에러',
                'host': self.host,
                'exception': str(e),
            })
            return

        return

    def update_document(self, document, doc_id, field, value, index):
        """문서를 저장한다."""
        # 서버 접속
        if self.elastic is None:
            self.open()

        if index is not None:
            self.index = index

        try:
            condition = "if (!ctx._source.{field}.contains(params.value)) ".format(field=field)
            condition += "{{ ctx._source.{field}.add(params.value) }}".format(field=field)

            body = {
                'script': {
                    'source': condition,
                    'lang': 'painless',
                    'params': {
                        'value': value
                    }
                },
                'upsert': document
            }

            self.elastic.update(
                index=index,
                doc_type='doc',
                id=doc_id,
                body=body
            )
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '업데이트 에러',
                'exception': str(e),
            })

        return True

    def save_document(self, document, index=None, delete=True):
        """문서를 저장한다."""
        # 서버 접속
        if self.elastic is None:
            self.open()

        if index is None:
            index = self.index

        # 버퍼링
        if document is not None:
            # 날짜 변환
            document = self.convert_datetime(document=document)

            if '_id' in document:
                document_id = document['_id']
                del document['_id']
            elif 'document_id' in document:
                document_id = document['document_id']
            else:
                document_id = datetime.now(self.timezone).isoformat()

            document['document_id'] = document_id

            if self.host not in self.bulk_data:
                self.bulk_data[self.host] = []

            # 기존 정보 삭제
            if delete is True:
                self.bulk_data[self.host].append({
                    'delete': {
                        '_id': document_id,
                        '_index': index,
                    }
                })

            # 저장 정보
            self.bulk_data[self.host].append({
                'update': {
                    '_id': document_id,
                    '_index': index,
                }
            })

            # 저장 문서
            self.bulk_data[self.host].append({
                'doc': document,
                'doc_as_upsert': self.insert,
            })

            # 버퍼링
            if self.bulk_size * 2 > len(self.bulk_data[self.host]):
                return True

        # 버퍼 크기 확인
        if self.host not in self.bulk_data or len(self.bulk_data[self.host]) == 0:
            return True

        # 버퍼 밀어내기
        self.flush()

        return True

    @staticmethod
    def json_default(value):
        """ 날자형을 문자로 변환한다."""
        if isinstance(value, datetime):
            return value.isoformat()

        raise TypeError('not JSON serializable')

    def flush(self):
        """버퍼에 남은 문서를 저장한다."""
        if self.elastic is None:
            return None

        if self.host not in self.bulk_data or len(self.bulk_data[self.host]) == 0:
            return None

        bulk_data = json.loads(json.dumps(self.bulk_data[self.host], default=self.json_default))
        self.bulk_data[self.host] = []

        try:
            response = self.elastic.bulk(
                index=self.index,
                body=bulk_data,
                refresh=True,
                params=self.params,
            )

            size = len(bulk_data)
            doc_id_list = []
            for doc in bulk_data:
                if 'update' in doc and '_id' in doc['update']:
                    doc_id_list.append(doc['update']['_id'])
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '저장 에러 (bulk)',
                'exception': str(e),
            })

            self.save_logs(doc_list=bulk_data, error_msg={'exception': str(e)})
            return False

        if 'errors' not in response:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'error 필드가 없음',
                'response': response,
            })
            return True

        try:
            if response['errors'] is False:
                self.logger.info(msg={
                    'level': 'INFO',
                    'message': '저장 성공',
                    'count': int(size / 2),
                })

                if len(doc_id_list) > 0:
                    for doc_id in doc_id_list[:10]:
                        self.logger.info(msg={
                            'level': 'INFO',
                            'message': '저장 성공',
                            'url': '{host}/{index}/_doc/{id}?pretty'.format(
                                host=self.host,
                                index=self.index,
                                id=doc_id,
                            ),
                        })
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '저장 성공 로깅 에러',
                'exception': str(e),
            })

            return False

        try:
            if response['errors'] is True:
                self.save_logs(doc_list=bulk_data, error_msg={
                    'message': '저장 에러',
                    'response': response['errors']
                })

                reason_list = []
                for item in response['items']:
                    if 'update' not in item:
                        continue

                    if 'error' not in item['update']:
                        continue

                    if 'reason' not in item['update']['error']:
                        continue

                    reason_list.append(item['update']['error']['reason'])

                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '저장 에러 (msg)',
                    'reason': reason_list,
                })
                return False
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '저장 에러 로깅 에러',
                'exception': str(e),
            })

            return False

        return True

    def save_logs(self, doc_list, error_msg):
        """ 저장 에러나는 문서를 로컬에 저장한다."""
        if isdir(self.log_path) is False:
            makedirs(self.log_path)

        dt = datetime.now(self.timezone)

        contents = {
            'host': self.host,
            'index': self.index,
            'date': dt.isoformat(),
            'error_msg': error_msg,
            'doc_list': doc_list,
        }

        filename = '{}/{}-{}.json'.format(self.log_path, self.index, dt.strftime('%Y%m%d-%H%M%S'))
        with open(filename, 'w') as fp:
            fp.write(json.dumps(contents, ensure_ascii=False, indent=2))

        return

    def dump(self, index=None, query=None, size=1000, limit=-1, only_source=True, stdout=False):
        """문서를 덤프 받는다."""
        if index is None:
            index = self.index

        count = 1
        sum_count = 0
        scroll_id = ''

        p_bar = None

        result = []
        while count > 0:
            hits, scroll_id, count, total = self.scroll(
                index=index,
                size=size,
                query=query,
                scroll_id=scroll_id,
            )

            if p_bar is None:
                p_bar = tqdm(
                    total=total,
                    desc='dump doc id list {index}'.format(index=index),
                    dynamic_ncols=True
                )
            p_bar.update(count)

            sum_count += count

            self.logger.info(msg={
                'level': 'INFO',
                'index': index,
                'count': count,
                'sum_count': sum_count,
                'total': total,
            })

            for item in hits:
                if stdout is True:
                    str_doc = json.dumps(item['_source'], ensure_ascii=False)
                    print(str_doc, flush=True)

                if only_source is True:
                    result.append(item['_source'])
                else:
                    result.append(item)

            if 0 < limit < sum_count:
                break

            # 종료 조건
            if count < size:
                break

        return result

    def scroll(self, scroll_id, query, index=None, size=1000):
        """스크롤 방식으로 데이터를 조회한다."""
        if index is None:
            index = self.index

        # 스크롤 아이디가 있다면 scroll 함수 호출
        if scroll_id == '':
            search_result = self.elastic.search(
                index=index,
                body=query,
                scroll='2m',
                size=size,
                params=self.params,
            )
        else:
            search_result = self.elastic.scroll(
                scroll_id=scroll_id,
                scroll='2m',
                params=self.params,
            )

        # 검색 결과 추출
        scroll_id = search_result['_scroll_id']

        hits = search_result['hits']

        total = hits['total']
        if isinstance(total, dict) and 'value' in total:
            total = total['value']

        count = len(hits['hits'])

        return hits['hits'], scroll_id, count, total

    def get_by_ids(self, id_list, index, source, result):
        """ 문서 아이디로 문서를 가져온다."""
        if len(id_list) == 0:
            return

        resp = self.elastic.mget(
            body={
                'docs': [{'_id': x} for x in id_list]
            },
            index=index,
            _source=source,
        )

        for n in resp['docs']:
            if '_source' not in n:
                continue

            result.append(n['_source'])

        return

    def get_id_list(self, index, size=5000, query_cond=None, limit=-1):
        """ elastic search 에 문서 아이디 목록을 조회한다. """
        result = {}
        if self.elastic.indices.exists(index) is False:
            return result

        count = 1
        sum_count = 0
        scroll_id = ''

        query = {
            '_source': ''
        }
        if query_cond is not None:
            query.update(query_cond)

        p_bar = None

        while count > 0:
            hits, scroll_id, count, total = self.scroll(
                index=index,
                size=size,
                query=query,
                scroll_id=scroll_id,
            )

            if p_bar is None:
                p_bar = tqdm(
                    total=total,
                    desc='dump doc id list {index}'.format(index=index),
                    dynamic_ncols=True
                )
            p_bar.update(count)

            sum_count += count

            log_msg = {
                'level': 'INFO',
                'index': index,
                'count': count,
                'sum_count': sum_count,
                'total': total,
            }
            self.logger.info(msg=log_msg)

            for item in hits:
                document_id = item['_id']

                if len(item['_source']) == 0:
                    result[document_id] = document_id
                else:
                    result[document_id] = item['_source']

            # 종료 조건
            if 0 < limit < sum_count:
                break

            if count < size:
                break

        return result

    def get_url_list(self, index, size=1000, date_range=None, query='', query_field=''):
        """ elastic search 에서 url 목록을 조회한다. """
        result = []

        count = 1
        sum_count = 0
        scroll_id = ''

        scroll_query = {}
        if query != '':
            scroll_query = json.loads(query)
        elif date_range is not None:
            token = date_range.split('~')

            scroll_query = {
                'query': {
                    'bool': {
                        'must': [
                            {
                                'range': {
                                    query_field: {
                                        'format': 'yyyy-MM-dd',
                                        'gte': token[0],
                                        'lte': token[1]
                                    }
                                }
                            }
                        ]
                    }
                }
            }

        while count > 0:
            hits, scroll_id, count, total = self.scroll(
                index=index,
                size=size,
                query=scroll_query,
                scroll_id=scroll_id,
            )

            sum_count += count

            self.logger.info(msg={
                'level': 'INFO',
                'index': index,
                'count': count,
                'sum_count': sum_count,
                'total': total,
            })

            for item in hits:
                result.append(item['_source'])

            # 종료 조건
            if count < size:
                break

        return result

    @staticmethod
    def save_cache(filename, cache_data):
        """데이를 피클로 저장한다."""
        with open(filename, 'wb') as fp:
            pickle.dump(cache_data, fp)

        return

    @staticmethod
    def load_cache(filename):
        """피클로 저장된 데이터를 반환한다."""
        result = {}
        if isfile(filename):
            with open(filename, 'rb') as fp:
                result = pickle.load(fp)

        return result

    def move_document(self, source_index, target_index, document_id, source_id=None, merge_column=None):
        """ 문서를 이동한다."""
        if source_id is None:
            source_id = document_id

        # 원본 문서 확인
        try:
            exists = self.elastic.exists(index=source_index, doc_type='doc', id=source_id)
            if exists is False:
                self.logger.info(msg={
                    'level': 'INFO',
                    'message': 'move document 문서 없음',
                    'source_index': source_index,
                    'source_id': source_id,
                    'document_id': document_id,
                })
                return
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'move document 문서 찾기 오류',
                'source_id': source_id,
                'document_id': document_id,
                'exception': str(e),
            })
            return

        # 원본 문서 읽기
        try:
            document = self.elastic.get(index=source_index, doc_type='_doc', id=source_id)

            if source_id != document_id:
                document['_source']['_id'] = document_id
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'move document 문서 읽기 오류',
                'source_id': source_id,
                'document_id': document_id,
                'exception': str(e),
            })
            return

        # 문서 병합
        if merge_column is not None:
            document = self.merge_doc(index=target_index, doc=document, column=merge_column)

        # 문서 저장
        self.save_document(document=document['_source'], index=target_index)
        self.flush()

        # 기존 문서 삭제
        try:
            self.elastic.delete(index=source_index, doc_type='doc', id=source_id)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'move document 문서 삭제 오류',
                'source_index': source_index,
                'source_id': source_id,
                'exception': str(e),
            })
            return

        return

    def merge_doc(self, index, doc, column):
        """이전에 수집한 문서와 병합"""
        doc_id = doc['_id']

        exists = self.elastic.exists(index=index, doc_type='_doc', id=doc_id)
        if exists is False:
            return doc

        try:
            resp = self.elastic.get(index=index, doc_type='_doc', id=doc_id)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '문서 병합 에러',
                'index': index,
                'column': column,
                'doc_id': doc_id,
                'exception': str(e),
            })
            return doc

        if '_source' not in resp:
            return doc

        prev_doc = resp['_source']

        for c in column:
            if c not in prev_doc or c not in doc:
                continue

            value = '{};{}'.format(prev_doc[c], doc[c])
            value = value.split(';')
            value = set(value)

            doc[c] = ';'.join(list(value))

        # 문서 병합
        prev_doc.update(doc)

        return prev_doc

    def exists(self, index, doc_id, list_index, list_id, merge_column=None):
        """상세 페이지가 크롤링 결과에 있는지 확인한다. 만약 있다면 목록 인덱스에서 완료(*_done)으로 이동한다."""
        exists_doc = self.elastic.exists(
            id=doc_id,
            index=index,
            doc_type='doc',
        )

        if exists_doc is True:
            self.move_document(
                source_index=list_index,
                target_index='{}_done'.format(list_index),
                source_id=list_id,
                document_id=doc_id,
                merge_column=merge_column,
            )
            return True

        return False

    def batch(self):
        """ 배치 작업을 수행한다."""
        args = self.init_arguments()

        self.host = args.host
        self.index = args.index
        self.http_auth = 'crawler:crawler2019'

        self.open()

        if args.export:
            self.dump(index=args.index, stdout=True)

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('-export', action='store_true', default=False, help='')

        parser.add_argument('-host', default='http://corpus.ncsoft.com:9200', help='elastic search 주소')
        parser.add_argument('-index', default=None, help='인덱스명')

        return parser.parse_args()


if __name__ == '__main__':
    ElasticSearchUtils(host=None, index=None).batch()
