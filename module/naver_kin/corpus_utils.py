#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
import sys
from os import listdir
from os.path import isdir, join

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class CorpusUtils(object):
    """크롤링 결과 추출"""

    def __init__(self):
        """ 생성자 """

    @staticmethod
    def save_to_excel(file_name, data, column_names):
        """ 크롤링 결과를 엑셀로 저장한다. """
        from openpyxl import Workbook

        status = []

        wb = Workbook()

        for path in data:
            count = '{:,}'.format(len(data[path]))
            status.append([path, count])

            ws = wb.create_sheet(path)

            if len(column_names) == 0:
                column_names = list(data[path][0].keys())

            ws.append(column_names)
            for doc in data[path]:
                lines = []
                for c in column_names:
                    v = doc[c]
                    if v is None:
                        v = ''

                    lines.append('{}'.format(v))

                ws.append(lines)

        # 통계 정보 저장
        ws = wb['Sheet']
        for row in status:
            ws.append(row)

        ws.title = 'status'

        wb.save(file_name)

        return

    def merge_question(self, data_path='detail.json.bz2', result_filename='detail.xlsx'):
        """ 네이버 지식인 질문 목록 결과를 취합한다. """
        # 파일 목록 추출
        file_list = []
        if isdir(data_path):
            for file in listdir(data_path):
                filename = join(data_path, file)
                if isdir(filename):
                    continue

                file_list.append(filename)

            file_list = sorted(file_list)
        else:
            file_list = [data_path]

        doc_index = {}
        columns = 'fullDirNamePath,docId,title,previewContents,tagList'.split(',')

        count = 0
        for file in file_list:
            doc_list = []
            if file.find('.bz2') > 0:
                with bz2.open(file, 'rb') as fp:
                    buf = []
                    for line in fp.readlines():
                        line = str(line, encoding='utf-8').strip()

                        buf.append(line)

                        if len(buf) > 0 and line == '}':
                            body = ''.join(buf)
                            doc_list.append(json.loads(body))

                            buf = []
            else:
                with open(file, 'r') as fp:
                    doc_list = json.loads(''.join(fp.readlines()))

            for doc in doc_list:
                path = 'etc'
                if 'fullDirNamePath' in doc:
                    path = doc['fullDirNamePath'].replace('Q&A > ', '')

                if 'category' in doc:
                    path = doc['category']

                if isinstance(path, list):
                    path = 'etc'

                if path not in doc_index:
                    doc_index[path] = []

                doc_index[path].append(doc)

                line = json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=4)
                logging.info(line)

                count += 1
                print('{} {:,}'.format(file, count), end='\r', flush=True, file=sys.stderr)

        # excel 저장
        self.save_to_excel(file_name=result_filename, data=doc_index, column_names=columns)

        return

    @staticmethod
    def elastic_scroll(elastic, scroll_id, index, size, query, sum_count):
        """"""
        params = {'request_timeout': 2 * 60}

        # 스크롤 아이디가 있다면 scroll 함수 호출
        if scroll_id == '':
            search_result = elastic.search(index=index, doc_type='doc', body=query, scroll='2m',
                                           size=size, params=params)
        else:
            search_result = elastic.scroll(scroll_id=scroll_id, scroll='2m', params=params)

        # 검색 결과 추출
        scroll_id = search_result['_scroll_id']

        hits = search_result['hits']

        total = hits['total']

        count = len(hits['hits'])

        sum_count += count
        logging.info(msg='{} {:,} {:,} {:,}'.format(index, count, sum_count, total))

        return hits['hits'], scroll_id, count, sum_count

    def dump_elastic_search(self, host='http://localhost:9200', index='crawler-naver-kin-detail'):
        """elastic-search 의 데이터를 덤프 받는다."""
        # 한번에 가져올 문서수
        size = 1000

        count = 1
        sum_count = 0
        scroll_id = ''

        # 서버 접속
        elastic = self.open_elastic_search(host=[host], index=index)
        if elastic is None:
            return

        while count > 0:
            hits, scroll_id, count, sum_count = self.elastic_scroll(
                elastic=elastic, scroll_id=scroll_id, index=index,
                size=size, query={}, sum_count=sum_count)

            for item in hits:
                line = json.dumps(item, ensure_ascii=False, sort_keys=True)
                print(line, flush=True)

            # 종료 조건
            if count < size:
                break

        return

    def export_detail(self):
        """"""
        host = 'http://localhost:9200'
        index = 'crawler-naver-kin-detail'

        # 한번에 가져올 문서수
        size = 1000

        count = 1
        sum_count = 0
        scroll_id = ''

        # 서버 접속
        elastic = self.open_elastic_search(host=[host], index=index)
        if elastic is None:
            return

        query = {
            '_source': 'category,question,detail_question,answer,answer_user'.split(','),
            'size': size
        }

        while count > 0:
            hits, scroll_id, count, sum_count = self.elastic_scroll(
                elastic=elastic, scroll_id=scroll_id, index=index,
                size=size, query=query, sum_count=sum_count)

            for item in hits:
                doc = item['_source']

                common = [
                    item['_id'],
                    doc['category'],
                    doc['question'],
                    doc['detail_question']
                ]

                for i in range(len(doc['answer'])):
                    try:
                        answer = [doc['answer_user'][i], doc['answer'][i]]
                        logging.info(msg='\t'.join(common + answer))
                    except Exception as e:
                        logging.error(msg='{}'.format(e))
                        pass

            # 종료 조건
            if count < size:
                break

        return

    def sync_id(self, index='crawler-naver-kin-detail'):
        """document_id 와 _id 가 형식에 맞지 않는 것을 바꾼다. """
        query = {
            '_source': 'd1Id,dirId,docId,document_id'.split(','),
            'size': '1000',
            'query': {
                'match_all': {}
            }
        }

        data_list, elastic = self.get_document_list(index=index, query=query, only_source=False, limit=-1)

        for item in data_list:
            doc = item['_source']

            if index == 'crawler-naver-kin-detail' and 'document_id' in doc:
                d_id = doc['document_id']
            else:
                if 'd1Id' not in doc:
                    doc['d1Id'] = str(doc['dirId'])[0]

                d_id = '{}-{}-{}'.format(doc['d1Id'], doc['dirId'], doc['docId'])

            if item['_id'].find('201807') == 0 or d_id != item['_id']:
                print(item)
                self.move_document(host=self.elastic_info['host'], source_index=index, target_index=index,
                                   document_id=d_id, source_id=item['_id'])

        return
