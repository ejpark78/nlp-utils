#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime

import pytz

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

        self.selenium = SeleniumUtils()

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
        self.elastic.save_document(document=doc, delete=False, index=index)

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '문서 저장 성공',
            'document_id': doc['document_id'],
            'content': doc['content'],
        })

        return
