#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from datetime import datetime
from glob import glob
from os.path import isdir

import pytz

from module.facebook.cache_utils import CacheUtils
from module.facebook.parser import FBParser
from utils.elasticsearch_utils import ElasticSearchUtils
from utils.logger import Logger
from utils.selenium_utils import SeleniumUtils


class FBBase(object):

    def __init__(self, params):
        super().__init__()

        self.params = params

        self.timezone = pytz.timezone('Asia/Seoul')

        self.logger = Logger()

        self.parser = FBParser()

        self.selenium = SeleniumUtils(
            login=self.params.login,
            headless=self.params.headless,
            user_data_path=self.params.user_data,
        )

        self.db = None
        if self.params.cache is not None:
            self.db = CacheUtils(
                filename=self.params.cache,
                use_cache=self.params.use_cache
            )

        self.elastic = None
        if self.params.index is not None:
            self.elastic = ElasticSearchUtils(
                host=self.params.host,
                index=self.params.index,
                log_path=self.params.log_path,
                http_auth=self.params.auth,
                split_index=True,
            )

    def save_post(self, doc, group_info):
        """추출한 정보를 저장한다."""
        doc['page'] = group_info['page']
        if 'page' not in doc or 'top_level_post_id' not in doc:
            return

        doc['_id'] = '{page}-{top_level_post_id}'.format(**doc)

        if 'meta' in group_info:
            doc.update(group_info['meta'])

        doc['curl_date'] = datetime.now(self.timezone).isoformat()

        index = None
        if 'index' in group_info:
            index = group_info['index']

        if self.elastic is not None:
            self.elastic.save_document(document=doc, delete=False, index=index)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '문서 저장 성공',
                'document_id': doc['document_id'],
                'content': doc['content'],
            })

        if self.db is not None:
            self.db.save_post(document=doc, post_id=doc['top_level_post_id'])

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '문서 저장 성공',
                'group_info': group_info,
                'content': doc['content'],
            })

        return

    @staticmethod
    def read_config(filename, with_comments=False):
        """설정파일을 읽어드린다."""
        file_list = filename.split(',')
        if isdir(filename) is True:
            file_list = []
            for f_name in glob('{}/*.json'.format(filename)):
                file_list.append(f_name)

        result = []
        for f_name in file_list:
            with open(f_name, 'r') as fp:
                if with_comments is True:
                    buf = ''.join([re.sub(r'^//', '', x) for x in fp.readlines()])
                else:
                    buf = ''.join([x for x in fp.readlines() if x.find('//') != 0])

                doc = json.loads(buf)
                result += doc['list']

        return result
