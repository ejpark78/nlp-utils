#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import pickle
import ssl
import sys
from datetime import datetime
from os.path import isfile

import pytz
import urllib3
from dateutil.parser import parse as parse_date
from elasticsearch import Elasticsearch
from elasticsearch.connection import create_ssl_context
from tqdm import tqdm

from etl.utils.logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)

logger = logging.getLogger()


class ElasticSearchUtils(object):
    """엘라스틱 서치 유틸"""

    def __init__(self, host, index=None, http_auth=None, bulk_size=1000, insert=True, tag=None, split_index=False,
                 mapping_filename=None):
        """ 생성자 """
        self.host = host

        self.http_auth = None
        if http_auth is not None:
            self.http_auth = (http_auth.split(':'))

        self.elastic = None

        self.index = self.get_target_index(
            tag=tag,
            index=index,
            split_index=split_index,
        )

        self.bulk_data = {}
        self.bulk_size = bulk_size

        self.insert = insert

        self.timezone = pytz.timezone('Asia/Seoul')

        self.mapping_filename = mapping_filename

        if self.host is not None:
            self.open()

    def create_index(self, elastic, index=None, filename=None):
        """인덱스를 생성한다."""
        if elastic is None:
            return False

        if filename is not None:
            self.mapping_filename = filename

        # 디폴트 맵핑 정보
        mapping = {
            'settings': {
                'number_of_shards': 3,
                'number_of_replicas': 2
            },
            'index.mapping.total_fields.limit': 20000,
        }

        # 매핑 파일이 있는 경우
        if self.mapping_filename is not None:
            if isfile(self.mapping_filename):
                with open(self.mapping_filename, 'rt') as fp:
                    mapping = json.loads(''.join(fp.readlines()))

        msg = {
            'level': 'MESSAGE',
            'message': '인덱스 생성',
            'index': index,
            'mapping_filename': filename,
            'mapping': mapping,
        }
        logger.log(level=MESSAGE, msg=LogMsg(msg))

        # 인덱스 생성
        try:
            elastic.indices.create(index=index, body=mapping)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '인덱스 생성 오류',
                'index': index,
                'mapping': mapping,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        return True

    @staticmethod
    def delete_index(elastic, index=None):
        """인덱스를 삭제한다."""
        if elastic is None:
            return False

        msg = {
            'level': 'MESSAGE',
            'message': '인덱스 삭제',
            'index': index,
        }
        logger.log(level=MESSAGE, msg=LogMsg(msg))

        # 인덱스 삭제
        try:
            elastic.indices.delete(index=index)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '인덱스 삭제 오류',
                'index': index,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        return

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

    @staticmethod
    def convert_datetime(document):
        """ 입력받은 문서에서 데이터 타입이 datetime 를 문자열로 변환한다."""
        for k in document:
            item = document[k]

            if isinstance(item, datetime):
                document[k] = item.isoformat()

        return document

    @staticmethod
    def get_ssl_verify_mode():
        """ """
        # https://github.com/elastic/elasticsearch-py/issues/712
        ssl_context = create_ssl_context()

        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        return ssl_context

    def open(self, host=None):
        """서버에 접속한다."""
        # https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch

        if host is not None:
            self.host = host

        # ssl_context = None
        # check_verify_mode = False
        #
        # if check_verify_mode is True:
        #     ssl_context = self.get_ssl_verify_mode()

        # host 접속
        try:
            self.elastic = Elasticsearch(
                hosts=self.host,
                timeout=30,
                http_auth=self.http_auth,
                # ssl_context=ssl_context,
                use_ssl=True,
                verify_certs=False,
                ssl_show_warn=False
            )
        except Exception as e:
            self.elastic = Elasticsearch(
                hosts=self.host,
                timeout=30,
                http_auth=self.http_auth,
                # ssl_context=ssl_context,
                use_ssl=True,
                verify_certs=False,
                ssl_show_warn=False
            )
            msg = {
                'level': 'ERROR',
                'message': '서버 접속 에러',
                'host': self.host,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))
            return

        if self.index is None:
            return

        try:
            if self.elastic.indices.exists(self.index) is False:
                self.create_index(self.elastic, self.index)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '인덱스 생성 에러',
                'host': self.host,
                'index': self.index,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))
            return

        return

    def get_index_list(self):
        """모든 인덱스 목록을 반환한다."""
        return [v for v in self.elastic.indices.get('*') if v[0] != '.']

    def get_column_list(self, index_list, column_type=None):
        """index 내의 field 목록을 반환한다."""
        result = []

        if type(index_list) is str:
            index_list = [index_list]

        for idx in index_list:
            m_info = self.elastic.indices.get_mapping(index=idx)

            if column_type is None:
                result += list(m_info[idx]['mappings']['properties'].keys())
            else:
                for k in m_info[idx]['mappings']['properties']:
                    item = m_info[idx]['mappings']['properties'][k]
                    if 'type' in item and item['type'] == column_type:
                        result.append(k)

        return list(set(result))

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
            log_msg = {
                'level': 'ERROR',
                'message': '업데이트 에러',
                'exception': str(e),
            }
            logger.error(msg=LogMsg(log_msg))

        return True

    def save_document(self, document, index=None, delete=False):
        """문서를 서버에 저장한다."""
        # 서버 접속
        if self.elastic is None:
            self.open()

        if index is not None:
            self.index = index

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
                document_id = datetime.now(tz=self.timezone).strftime('%Y%m%d_%H%M%S.%f')

            document['document_id'] = document_id

            if self.host not in self.bulk_data:
                self.bulk_data[self.host] = []

            # 삭제
            if delete is True:
                self.bulk_data[self.host].append({
                    'delete': {
                        '_index': self.index,
                        '_id': document_id,
                    }
                })

            self.bulk_data[self.host] += [
                {
                    'update': {
                        '_index': self.index,
                        '_id': document_id,
                    }
                }, {
                    'doc': document,
                    'doc_as_upsert': self.insert,
                }
            ]

            # 버퍼링
            if self.bulk_size * 2 > len(self.bulk_data[self.host]):
                return True

        # 버퍼 크기 확인
        if self.host not in self.bulk_data or len(self.bulk_data[self.host]) == 0:
            return True

        # 버퍼 밀어내기
        self.flush()

        return True

    def flush(self):
        """버퍼를 비운다."""
        if self.elastic is None:
            return None

        if self.host not in self.bulk_data:
            return None

        response = None

        doc_list = {}
        doc_id_list = []

        params = {'request_timeout': 2 * 60}

        try:
            doc_id = ''
            doc_id_list = []
            for doc in self.bulk_data[self.host]:
                if 'update' in doc and '_id' in doc['update']:
                    doc_id = doc['update']['_id']
                    doc_id_list.append(doc_id)
                else:
                    doc_list[str(doc_id)] = doc

            if len(doc_list) == 0:
                return None

            response = self.elastic.bulk(
                index=self.index,
                body=self.bulk_data[self.host],
                refresh=True,
                params=params,
            )
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '저장 에러 (bulk)',
                'host': self.host,
                'index': self.index,
                'response': response,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        size = len(self.bulk_data[self.host])

        msg = {
            'level': 'INFO',
            'size': size,
        }
        logger.info(msg=LogMsg(msg))

        self.bulk_data[self.host] = []

        if response is None:
            return

        try:
            error = '성공'
            if response['errors'] is True:
                error = '에러'

            if error != '에러':
                msg = {
                    'level': 'INFO',
                    'message': '저장 성공',
                    'bulk_size': size,
                }
                logger.info(msg=LogMsg(msg))
            else:
                msg = {
                    'level': 'ERROR',
                    'message': '저장 에러 (msg)',
                    'reason': []
                }

                for items in response['items']:
                    if 'update' not in items:
                        continue

                    if 'error' in items['update'] and 'reason' in items['update']['error'] and '_id' in items['update']:
                        msg['reason'].append({
                            'doc_id': items['update']['_id'],
                            'reason': items['update']['error']['reason']
                        })

                logger.error(msg=LogMsg(msg))

            if len(doc_id_list) > 0:
                msg = {
                    'level': 'INFO',
                    'message': '저장 성공',
                    'doc_url': [],
                }

                for doc_id in doc_id_list[:10]:
                    msg['doc_url'].append(
                        '{host}/{index}/doc/{doc_id}?pretty'.format(
                            host=self.host,
                            index=self.index,
                            doc_id=doc_id,
                        )
                    )

                logger.info(msg=LogMsg(msg))
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '저장 에러 (메세지 생성)',
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        return

    def scroll(self, index, scroll_id, query, size=1000):
        """스크롤 API를 호출한다."""
        if index is None:
            index = self.index

        params = {
            'request_timeout': 10 * 60
        }

        # 스크롤 아이디가 있다면 scroll 함수 호출
        if scroll_id == '':
            search_result = self.elastic.search(
                index=index,
                body=query,
                scroll='2m',
                size=size,
                params=params,
            )
        else:
            search_result = self.elastic.scroll(
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

        count = len(hits['hits'])

        return hits['hits'], scroll_id, count, total

    def get_id_list(self, index, cache='', size=5000, query_cond=None, desc=None):
        """문서 아이디 목록을 조회한다. """
        if cache != '':
            result = self.load_cache(cache)

            if len(result) > 0:
                return result

        result = {}
        if self.elastic.indices.exists(index) is False:
            return result

        count = 1
        sum_count = 0
        scroll_id = ''

        query = {
            '_source': '',
        }

        if query_cond is not None:
            query.update(query_cond)

        p_bar = None
        if desc is None:
            desc = 'dump doc id list {index}'.format(index=index)

        while count > 0:
            hits, scroll_id, count, total = self.scroll(
                size=size,
                index=index,
                query=query,
                scroll_id=scroll_id,
            )

            if p_bar is None:
                p_bar = tqdm(total=total, desc=desc, dynamic_ncols=True)

            p_bar.update(count)

            sum_count += count

            msg = {
                'level': 'INFO',
                'index': index,
                'count': count,
                'sum_count': sum_count,
                'total': total,
            }
            logger.info(msg=LogMsg(msg))

            for item in hits:
                document_id = item['_id']

                if len(item['_source']) == 0:
                    result[document_id] = document_id
                else:
                    result[document_id] = item['_source']

            # 종료 조건
            if count < size:
                break

        if p_bar is not None:
            p_bar.close()

        if cache != '':
            self.save_cache(cache_data=result, filename=cache)

        return result

    def get_by_ids(self, id_list, index, source, result):
        """ 문서 아이디로 문서를 가져온다."""
        if len(id_list) == 0:
            return

        doc_list = self.elastic.mget(
            index=index,
            _source=source,
            body={
                'docs': [{'_id': x} for x in id_list]
            },
        )

        for n in doc_list['docs']:
            if '_source' not in n:
                continue

            doc = n['_source']
            doc_id = n['_id']

            if len(doc) == 0:
                continue

            doc['document_id'] = doc_id
            result.append(doc)

        return

    @staticmethod
    def save_cache(filename, cache_data):
        """캐쉬로 저장한다."""
        import pickle

        with open(filename, 'wb') as fp:
            pickle.dump(cache_data, fp)

        return

    @staticmethod
    def load_cache(filename):
        """저장된 캐쉬를 로드한다."""
        result = {}
        if isfile(filename):
            with open(filename, 'rb') as fp:
                result = pickle.load(fp)

        return result

    def import_data(self, index, id_field=None, use_year_tag=False):
        """데이터를 서버에 저장한다."""
        idx_cache = {}

        count = 0
        for line in sys.stdin:
            doc = json.loads(line)

            if doc is None:
                continue

            count += 1
            if count % 1000 == 0:
                print('{} {:,}'.format(index, count))

            if id_field is not None and id_field in doc:
                doc['_id'] = doc[id_field]

            # 날짜 변환
            for k in ['date', 'curl_date', 'update_date', 'insert_date', '@timestamp']:
                if k not in doc:
                    continue

                if isinstance(doc[k], dict) and '$date' in doc[k]:
                    doc[k] = doc[k]['$date']

                if isinstance(doc[k], str):
                    if doc[k] == '' or doc[k] == '|':
                        del doc[k]
                        continue

                    dt = parse_date(doc[k])

                    # 시간대를 변경한다.
                    if dt.tzinfo is not None:
                        dt = dt.astimezone(self.timezone)
                    elif doc[k].find('+00:00') > 0:
                        dt = dt.astimezone(self.timezone)
                    elif doc[k].find('+09:00') < 0:
                        dt = self.timezone.localize(dt)

                    doc[k] = dt

            target_idx = index
            if use_year_tag is True:
                try:
                    target_idx = '{index}-{year}'.format(index=index, year=doc['date'].year)

                    if target_idx not in idx_cache:
                        idx_cache[target_idx] = self.get_id_list(index=target_idx)

                    # 중복 아이디 확인
                    if doc['document_id'] in idx_cache[target_idx]:
                        continue
                except Exception as e:
                    print(e)

            self.save_document(document=doc, index=target_idx)

        self.flush()

        return

    def export(self, index, query=None, size=1000, result=None, limit=0, include_id=False):
        """데이터를 서버에서 덤프 받는다."""
        if query is None:
            query = {}

        if isinstance(query, str):
            query = json.loads(query)

        self.index = index

        count = 1
        sum_count = 0
        scroll_id = ''

        p_bar = None

        while count > 0:
            hits, scroll_id, count, total = self.scroll(
                index=index,
                size=size,
                query=query,
                scroll_id=scroll_id,
            )

            if p_bar is None:
                p_bar = tqdm(total=total, desc='dump: ' + index, dynamic_ncols=True)

            p_bar.update(count)

            sum_count += count

            msg = {
                'level': 'INFO',
                'index': index,
                'count': count,
                'sum_count': sum_count,
                'total': total,
            }
            logger.info(msg=LogMsg(msg))

            for item in hits:
                if result is None:
                    document = json.dumps(item['_source'], ensure_ascii=False, sort_keys=True)
                    print(document, flush=True)

                    # print(json.dumps({'index': {'_index': item['_index'], '_id': item['_id']}}, ensure_ascii=False), flush=True)
                    # print(json.dumps({'doc': item['_source']}, ensure_ascii=False), flush=True)
                else:
                    if include_id is True:
                        if 'document_id' not in item['_source']:
                            item['_source']['document_id'] = item['_id']

                    result.append(item['_source'])

            # 종료 조건
            if count < size:
                break

            if 0 < limit <= len(result):
                break

        if p_bar is not None:
            p_bar.close()

        return

    def delete_doc_by_id(self, index, id_list):
        """아이디로 문서를 삭제한다."""
        self.elastic.delete_by_query(
            index=index,
            body={
                'query': {
                    'ids': {
                        'values': id_list
                    }
                }
            }
        )

        return

    def rename_docs(self, error_ids, index):
        """ """

        def parse_url(url):
            from urllib.parse import urlparse, parse_qs

            url_info = urlparse(url)

            query = parse_qs(url_info.query)
            for key in query:
                query[key] = query[key][0]

            return query

        step = 500
        size = len(error_ids)

        for i in tqdm(range(0, size, step), dynamic_ncols=True):
            st, en = (i, i + step - 1)
            if en > size:
                en = size + 1

            doc_list = []
            self.elastic.get_by_ids(
                id_list=error_ids[st:en],
                index=index,
                source=None,
                result=doc_list,
            )

            bulk_data = []
            for doc in doc_list:
                if 'url' not in doc:
                    continue

                # src_id 삭제
                bulk_data.append({
                    'delete': {
                        '_id': doc['document_id'],
                        '_index': index,
                    }
                })

                doc_id = '{oid}-{aid}'.format(**parse_url(doc['url']))
                flag = self.elastic.elastic.exists(index=index, id=doc_id, doc_type='_doc')
                if flag is True:
                    continue

                # 문서 저장
                doc['document_id'] = doc_id

                bulk_data.append({
                    'update': {
                        '_id': doc_id,
                        '_index': index,
                    }
                })

                bulk_data.append({
                    'doc': doc,
                    'doc_as_upsert': True,
                })

            self.bulk_data[self.elastic.host] = bulk_data
            self.flush()

        return

    @staticmethod
    def simplify_nlu_wrapper(doc_list):
        """ """
        result = []
        for doc in tqdm(doc_list):
            if 'nlu_wrapper' not in doc:
                continue

            for k in doc['nlu_wrapper']:
                buf = {}
                for item in doc['nlu_wrapper'][k]:
                    for c in item:
                        if c not in buf:
                            buf[c] = ''

                        if isinstance(item[c], list):
                            buf[c] += '\n'.join(item[c])
                        else:
                            buf[c] += item[c]

                row = {
                    'document_id': doc['document_id'],
                    'date': doc['date'],
                    'column': k,
                }
                row.update(buf)

                result.append(row)

        return result

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('--import_data', action='store_true', default=False, help='')
        parser.add_argument('--index_list', action='store_true', default=False, help='')
        parser.add_argument('--use_year_tag', action='store_true', default=False, help='')

        parser.add_argument('--export', action='store_true', default=False, help='')

        parser.add_argument('--host', default='https://corpus.ncsoft.com:9200', help='elastic search 주소')
        parser.add_argument('--index', default=None, help='인덱스명')
        parser.add_argument('--auth', default=None, help='인증')

        parser.add_argument('--query', default=None, help='query')
        parser.add_argument('--date', default='2018-01', help='date')
        parser.add_argument('--field', default='date', help='date')
        parser.add_argument('--id_field', default=None, help='id_field')
        parser.add_argument('--filename', default=None, help='인덱스 정보 파일명')
        parser.add_argument('--mapping', default=None, help='맵핑 파일')

        return parser.parse_args()


def main():
    """메인"""
    args = ElasticSearchUtils.init_arguments()

    utils = ElasticSearchUtils(host=args.host, http_auth=args.auth)

    if args.index_list:
        result = utils.get_index_list()
        print('\n'.join(result))

    if args.import_data:
        utils.import_data(
            index=args.index,
            id_field=args.id_field,
            use_year_tag=args.use_year_tag,
        )

    if args.export:
        utils.export(index=args.index, query=args.query)

    return


if __name__ == '__main__':
    main()
