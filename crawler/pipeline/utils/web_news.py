#!./venv/bin/python3
# -*- coding: utf-8 -*-
"""NLP 기반 기술"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from datetime import datetime
from datetime import timezone, timedelta

import pytz
from dateutil.parser import parse as parse_date

from config import plugins
from logging_format import LogMessage as LogMsg
from utils.nlu_wrapper_utils import NLUWrapperUtils

MESSAGE = 25
logger = logging.getLogger()


class WebNewsUtils(object):
    """코퍼스 전처리 유틸"""

    def __init__(self):
        """생성자"""
        self.timezone = pytz.timezone('Asia/Seoul')
        self.kst_timezone = timezone(timedelta(hours=9))

        self.nlu_wrapper = NLUWrapperUtils()

    def remove_date_column(self, document):
        """날짜 필드를 확인해서 날짜 파싱 오류일 경우, 날짜 필드를 삭제한다."""
        if 'date' not in document:
            return

        if document['date'] == '':
            del document['date']
            return

        if isinstance(document['date'], str):
            try:
                dt = parse_date(document['date'])
                document['date'] = dt.replace(tzinfo=self.kst_timezone)
            except Exception as e:
                msg = {
                    'level': 'ERROR',
                    'message': '날짜 파싱 에러: date 필드 삭제',
                    'debug_info': plugins['debug_info'],
                    'exception': str(e),
                }
                logger.error(msg=LogMsg(msg))

                del document['date']

        return

    def batch(self, document, module_list):
        """하나의 기사를 코퍼스 전처리 한다."""
        self.remove_date_column(document=document)

        result = {}
        for module in module_list:
            r = self.batch_one_module(document=document, module=module)
            result.update(r)

        return result

    def batch_one_module(self, document, module):
        """하나의 기사를 코퍼스 전처리 한다."""
        result = {}

        # 제목 처리
        if 'title' in document and document['title'] != '':
            r = self.nlu_wrapper.batch(text=document['title'], option=module['option'])
            result['title'] = r

        # 이미지 자막 처리
        if 'image_list' in document:
            for item in document['image_list']:
                if 'caption' in item and item['caption'] != '':
                    sentence = item['caption']

                    if isinstance(sentence, list):
                        buf = []
                        for sent in sentence:
                            if sent == '':
                                continue

                            r = self.nlu_wrapper.batch(text=sent, option=module['option'])
                            buf += r

                        result['caption'] = buf
                    elif isinstance(sentence, str):
                        r = self.nlu_wrapper.batch(text=sentence, option=module['option'])
                        result['caption'] = r

        # 기사 본문 처리
        if 'content' in document:
            buf = []
            for text in document['content'].split('\n'):
                text = text.strip()
                if text == '':
                    continue

                buf += self.nlu_wrapper.batch(text=text, option=module['option'])

            result['content'] = buf

        module['option'].update({
            'date': datetime.now(tz=self.timezone).isoformat()
        })

        result['option'] = module['option']

        if 'result' in module:
            document[module['result']] = result
        else:
            document['nlu_wrapper'] = result

        return document
