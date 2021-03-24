#!./venv/bin/python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import sys

import requests
import urllib3

from config import config, plugins
from logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MESSAGE = 25

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(
    level=MESSAGE,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger()


class NLUWrapperUtils(object):
    """NLU Wrapper 유틸"""

    def __init__(self):
        """생성자"""

    def batch(self, text, option, timeout=30):
        """nlu wrapper 호출"""
        result = []

        if isinstance(text, str) is False:
            msg = {
                'level': 'ERROR',
                'message': 'NLU Wrapper 에러: 문장이 문자열이 아님',
                'sentence': text,
            }
            logger.error(msg=LogMsg(msg))

            return result

        url = config['nlu_wrapper']

        if 'SBD_crf' in option['module']:
            text = text.replace(r'\n', ' ')

        # POST 메세지
        if 'SBD' in option['module'] or 'SBD_crf' in option['module']:
            post_data = {
                'nlu_wrapper': {
                    'option': option
                },
                'doc': [{
                    'contents': text
                }]
            }
        else:
            post_data = {
                'nlu_wrapper': {
                    'option': option
                },
                'doc': [
                    {
                        'sentences': [{
                            'text': text
                        }]
                    }
                ]
            }

        # rest api 호출
        headers = {'Content-Type': 'application/json'}

        try:
            resp = requests.post(url=url, json=post_data, headers=headers, timeout=timeout).json()
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'NLU Wrapper 호출 에러',
                'url': url,
                'post_data': post_data,
                'debug_info': plugins['debug_info'],
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

            return result

        # 결과 취합
        try:
            result = self.parse_nlu_wrapper_resp(resp=resp)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'NLU Wrapper 결과 취합 에러',
                'url': url,
                'resp': resp,
                'post_data': post_data,
                'debug_info': plugins['debug_info'],
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        return result

    @staticmethod
    def parse_nlu_wrapper_resp(resp):
        """ 결과를 파싱한다."""
        dep_columns = ['index', 'head', 'morp', 'pos', 'func']

        result = []
        for doc in resp['doc']:
            for sentence in doc['sentences']:
                item = {
                    'text': '',
                    'morp_str': '',
                    'ne_str': '',
                    'depen_str': [],
                    'time_results': [],
                }

                for k in item.keys():
                    if k not in sentence:
                        continue

                    item[k] = sentence[k]

                # 결과 변환
                # 시간 필드 변경
                if len(item['time_results']) > 0:
                    item['times_str'] = json.dumps(item['time_results'], ensure_ascii=False)

                del item['time_results']

                # depen_str 변환
                if len(item['depen_str']) > 0:
                    depen = []
                    for dep in item['depen_str']:
                        depen.append(dict(zip(dep_columns, dep)))

                    item['depen_str'] = json.dumps(depen, ensure_ascii=False)
                else:
                    del item['depen_str']

                result.append(item)

        return result
