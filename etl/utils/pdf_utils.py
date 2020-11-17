#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re

import pandas as pd
from glob import glob
from pdftotext import PDF
from tqdm import tqdm


class PdfUtils(object):
    """pdf 유틸"""

    def __init__(self):
        """생성자"""

    @staticmethod
    def init_arguments():
        """옵션 설정"""
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('-compare', action='store_true', default=False, help='')
        parser.add_argument('-import_data', action='store_true', default=False, help='')

        parser.add_argument('-f', default=None, help='')

        return parser.parse_args()

    def batch(self):
        """메인"""
        path = '../data/날씨데이터/2018_단기예보/*.pdf'

        for f in tqdm(glob(path)):
            with open(f, 'rb') as fp:
                page_list = PDF(fp)

            buf = ''
            for page in page_list:
                if page.find('단 기 예 보 [육상]') > 0:
                    break

                buf += page

            item = {
                '오늘': [],
                '내일': [],
                '모레': [],
                '날씨종합': [],
            }

            buf = re.sub(r',\n', ', ', buf)

            when = ''
            for line in buf.split('\n'):
                if line.find('※') == 0:
                    continue

                if line.find('       서울  일출 ') > 0:
                    continue

                if line.find('오 늘 [') > 0:
                    when = '오늘'
                    continue
                elif line.find('내 일 [') > 0:
                    when = '내일'
                    continue
                elif line.find('모 레 [') > 0:
                    when = '모레'
                    continue
                elif line.find('날씨종합') > 0:
                    when = '날씨종합'
                    continue

                if when == '':
                    continue

                for k in '※,     -,       (내일),      인천     만조'.split(','):
                    line = line.split(k)[0]

                line = line.rstrip()

                item[when].append(line)

            buf = []
            for when in item:
                f_token = f.replace('rpt_wid_day_', '').replace('.pdf', '').split('/')

                for line in item[when]:
                    buf.append({
                        'path': f_token[-2],
                        'filename': f_token[-1],
                        'when': when,
                        'text': line
                    })

            df = pd.DataFrame(buf)
            if len(df) == 0:
                continue

            df['filename,path,when,text'.split(',')].to_excel(f.replace('.pdf', '.xlsx'), index=False)

        return


if __name__ == '__main__':
    PdfUtils().batch()
