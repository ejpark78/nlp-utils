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

from utils.logger import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MESSAGE = 25

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)

logger = logging.getLogger()


class NLUWrapperUtils(object):
    """NLU Wrapper 유틸"""

    def __init__(self):
        """생성자"""

    @staticmethod
    def batch(utils, index, text, option, timeout, url):
        """nlu wrapper 호출"""
        result = []

        if 'SBD_crf' in option['module']:
            text = text.replace(r'\n', ' ')

        # POST 메세지
        if 'SBD' in option['module'] or 'SBD_crf' in option['module']:
            doc = []
            if isinstance(text, str):
                doc = [{
                    'contents': text
                }]
            else:
                for t in text:
                    doc.append({
                        'contents': t
                    })

            post_data = {
                'nlu_wrapper': {
                    'option': option
                },
                'doc': doc
            }
        else:
            doc = []
            if isinstance(text, str):
                doc = [
                    {
                        'sentences': [{
                            'text': text
                        }]
                    }
                ]
            else:
                for t in text:
                    doc.append(
                        {
                            'sentences': [{
                                'text': t
                            }]
                        }
                    )

            post_data = {
                'nlu_wrapper': {
                    'option': option
                },
                'doc': doc
            }

        # rest api 호출
        try:
            resp = requests.post(url=url, json=post_data, timeout=timeout).json()
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'NLU Wrapper 호출 에러',
                'url': url,
                'post_data': post_data,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

            return {
                'index': index,
                'result': result
            }

        # 결과 취합
        try:
            result = utils.parse_nlu_wrapper_resp(resp=resp)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'NLU Wrapper 결과 취합 에러',
                'url': url,
                'resp': resp,
                'post_data': post_data,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        return {
            'index': index,
            'result': result
        }

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

    def text_process(self, df, text_column):
        """ 텍스트 전처리"""
        from multiprocessing import Pool
        from tqdm.autonotebook import tqdm

        max_core = 128
        pool = Pool(processes=max_core)

        pool_list = []

        df.loc[:, 'nlu_wrapper'] = ''

        option = {
            'domain': 'common',
            'style': 'literary',
            'module': ['POS']
        }

        url = 'http://172.20.78.250:30000'
        timeout = 120

        for i, row in tqdm(df.iterrows(), total=len(df)):
            text_list = [x for x in row[text_column].split('\n') if x.strip() != '']

            p = pool.apply_async(
                self.batch,
                args=(self, i, text_list, option, timeout, url, )
            )
            pool_list.append(p)

            if len(pool_list) >= max_core:
                pool.close()
                pool.join()

                for r in tqdm(pool_list, desc='결과 취합'):
                    resp = r.get()
                    df.at[resp['index'], 'nlu_wrapper'] = resp['result']

                pool_list = []
                pool = Pool(processes=max_core)

        pool.close()
        pool.join()

        for r in tqdm(pool_list, desc='결과 취합'):
            resp = r.get()
            df.at[resp['index'], 'nlu_wrapper'] = resp['result']

        return df

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-filename', default=None, help='')

        return parser.parse_args()


def main():
    """"""
    utils = NLUWrapperUtils()

    args = utils.init_arguments()

    option = {
        'domain': 'common',
        'style': 'literary',
        'module': ['POS']
    }

    url = 'http://172.20.78.250:30000'
    timeout = 120

    doc_idx = {}
    text_list = []
    with open(args.filename, 'r') as fp:
        for l in fp.readlines():
            doc = json.loads(l)

            text = doc['korean'] = doc['korean'].strip()

            doc_idx[text] = doc
            text_list.append(text)

    resp = utils.batch(utils, 0, text_list, option, timeout, url)

    for item in resp['result']:
        text = item['text']
        if text not in doc_idx:
            continue

        doc = doc_idx[text]
        doc['korean_morp'] = item['morp_str']

    with open(args.filename + '.out', 'w') as fp:
        for text in doc_idx:
            if text not in doc_idx:
                continue

            l = json.dumps(doc_idx[text], ensure_ascii=False) + '\n'

            fp.write(l)

    return


if __name__ == '__main__':
    main()
