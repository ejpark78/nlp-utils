#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from module.naver_terms.term_list import TermList

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


def init_arguments():
    """ 옵션 설정 """
    import argparse

    parser = argparse.ArgumentParser()

    # 크롤링
    parser.add_argument('-term_list', action='store_true', default=False, help='목록 크롤링')

    # 파라메터
    parser.add_argument('-host', default='http://localhost:9200', help='elastic-search 주소')
    parser.add_argument('-index', default='question_list', help='인덱스명')
    parser.add_argument('-match_phrase', default='{"fullDirNamePath": "주식"}', help='검색 조건')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    if args.term_list:
        TermList().batch()

    return


if __name__ == '__main__':
    main()
