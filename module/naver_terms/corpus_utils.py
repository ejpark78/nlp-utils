#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from module.common_utils import CommonUtils
from module.config import Config
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
        self.job_id = 'naver_terms'
        self.cfg = Config(job_id=self.job_id)

        self.job_info = self.cfg.job_info['term_list']
        self.common_utils = CommonUtils()

    def dump(self):
        """"""
        import re

        # 데이터 덤프
        elastic_utils = ElasticSearchUtils(host=self.job_info['host'], index=self.job_info['index'],
                                           bulk_size=20)

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
        columns = ['document_id', 'category', 'hit_view', 'like_count', 'name', 'name_etc', 'define', 'detail_link']
        self.common_utils.save_excel(filename='{}.xlsx'.format(self.job_info['index']),
                                     data=data, columns=columns)
        return
