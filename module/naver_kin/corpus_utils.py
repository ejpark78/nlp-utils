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

from module.config import Config
from module.common_utils import CommonUtils
from module.elasticsearch_utils import ElasticSearchUtils

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class CorpusUtils(object):
    """크롤링 결과 추출"""

    def __init__(self):
        """ 생성자 """
        self.job_id = 'naver_kin'
        self.cfg = Config(job_category='naver', job_id=self.job_id)

        self.common_utils = CommonUtils()

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
        self.common_utils.save_excel(filename=result_filename, data=doc_index, columns=columns)

        return

    def sync_id(self, index='crawler-naver-kin-detail'):
        """document_id 와 _id 가 형식에 맞지 않는 것을 바꾼다. """

        job_info = self.cfg.job_info['detail']

        query = {
            '_source': 'd1Id,dirId,docId,document_id'.split(','),
            'size': '1000',
            'query': {
                'match_all': {}
            }
        }

        elastic_utils = ElasticSearchUtils(
            host=job_info['host'],
            index=job_info['index'],
            bulk_size=10,
            http_auth=job_info['http_auth'],
        )

        data_list = elastic_utils.dump(index=index, query=query, only_source=False, limit=5000)

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
                elastic_utils.move_document(source_index=index, target_index=index,
                                            document_id=d_id, source_id=item['_id'])

        return
