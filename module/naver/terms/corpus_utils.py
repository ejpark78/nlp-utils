#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from datetime import datetime

from module.config import Config
from module.utils.elasticsearch_utils import ElasticSearchUtils

MESSAGE = 25
logging_opt = {
    'format': '[%(levelname)-s] %(message)s',
    'handlers': [logging.StreamHandler()],
    'level': MESSAGE,

}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)


class CorpusUtils(object):
    """크롤링 결과 추출"""

    def __init__(self):
        """ 생성자 """
        self.job_id = 'naver_terms'
        self.cfg = Config(job_category='naver', job_id=self.job_id)

        self.job_info = self.cfg.job_info['term_list']

    def dump(self):
        """"""
        import re

        # 데이터 덤프
        elastic_utils = ElasticSearchUtils(
            host=self.job_info['host'],
            index=self.job_info['index'],
            bulk_size=20,
            http_auth=self.job_info['http_auth'],
        )

        doc_list = elastic_utils.dump()

        # 카테고리별로 분리
        data = {}
        for doc in doc_list:
            if 'name' in doc and doc['name'].find('['):
                name = doc['name']
                doc['name'] = re.sub('\[.+\]', '', name)
                doc['name_etc'] = re.sub('^.+\[(.+)\]', '\g<1>', name)

            category = 'etc'
            if 'category' in doc:
                category = doc['category']

            if category not in data:
                data[category] = []

            data[category].append(doc)

        # 데이터 저장
        date_tag = datetime.now().strftime('%Y-%m-%d')

        columns = ['document_id', 'category', 'hit_view', 'like_count', 'name', 'name_etc', 'define', 'detail_link']
        self.save_excel(filename='{}-{}.xlsx'.format(self.job_info['index'], date_tag),
                        data=data, columns=columns)
        return

    @staticmethod
    def save_excel(filename, data, columns):
        """ 크롤링 결과를 엑셀로 저장한다. """
        from openpyxl import Workbook

        status = []
        wb = Workbook()

        for path in data:
            count = '{:,}'.format(len(data[path]))
            status.append([path, count])

            ws = wb.create_sheet(path.replace('/', '-'))

            if len(columns) == 0:
                columns = list(data[path][0].keys())

            ws.append(columns)
            for doc in data[path]:
                lines = []
                for c in columns:
                    v = ''
                    if c in doc:
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

        # 파일 저장
        wb.save(filename)

        return
