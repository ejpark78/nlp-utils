#!./venv/bin/python3
# -*- coding: utf-8 -*-
"""NLP 기반 기술"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from config import plugins
from utils.text import TextUtils
from utils.web_news import WebNewsUtils

MESSAGE = 25
logger = logging.getLogger()


class CorpusPipelineUtils:
    """코퍼스 전처리 유틸"""

    def __init__(self):
        """생성자"""
        self.init_module = [{
            "name": "nlu_wrapper",
            "option": {
                "domain": "economy",
                "style": "literary",
                "module": ["SBD_crf", "POS", "NER"]
            },
            "column": "content",
            "result": "nlu_wrapper"
        }]

        self.default_module = [{
            "name": "nlu_wrapper",
            "option": {
                "domain": "economy",
                "style": "literary",
                "module": ["SBD_crf", "POS", "NER"]
            },
            "column": "content",
            "result": "nlu_wrapper"
        }]

        plugins['list'] = []
        plugins['debug_info'] = {}

    @staticmethod
    def set_debug_info(document):
        """디버깅 정보를 채운다."""
        plugins['debug_info'] = {}

        for k in ['document_id', '_id', 'url', 'date']:
            if k in document:
                plugins['debug_info'][k] = document[k]

        return

    def batch(self, payload):
        """ 문서 종류(web_news, text, bbs)에 따라 전처리 한다."""
        text_utils = TextUtils()
        web_news_utils = WebNewsUtils()

        document = payload['document']

        self.set_debug_info(document=document)

        if 'module' not in payload:
            payload['module'] = self.default_module

        # 문서 종류 식별: web_news, text
        doc_type = 'web_news'
        if 'doc_type' in payload:
            doc_type = payload['doc_type']

        # 입력된 문서 목록 혹은 문서 하나를 분석한다.
        document_list = document
        if isinstance(document, list) is False:
            document_list = [document]

        doc_list = []
        for doc in document_list:
            if doc_type == 'web_news':
                result_doc = web_news_utils.batch(document=doc, module_list=payload['module'])
            else:
                result_doc = text_utils.batch(document=doc, module_list=payload['module'])

            if len(result_doc) > 0:
                doc_list.append(result_doc)

        # 후처리 실행
        if len(doc_list) > 0:
            self.post_process(payload=payload, document=doc_list)

        return document

    @staticmethod
    def post_process(payload, document):
        """배치 작업을 실행한다."""
        from utils.elasticsearch_utils import ElasticSearchUtils

        elastic = ElasticSearchUtils()

        # 문서 저장
        if 'elastic' in payload:
            info = payload['elastic']

            # 데이터 저장
            elastic.save_document(
                document=document,
                elastic_info=info,
            )

        return
