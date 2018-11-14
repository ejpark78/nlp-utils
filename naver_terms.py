#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from module.naver_terms.term_list import TermList
from module.naver_terms.detail import TermDetail
from module.naver_terms.corpus_utils import CorpusUtils

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
    parser.add_argument('-detail', action='store_true', default=False, help='본문 크롤링')
    parser.add_argument('-dump', action='store_true', default=False, help='크롤링 결과 덤프')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    if args.term_list:
        TermList().batch()

    if args.detail:
        TermDetail().batch()

    if args.dump:
        CorpusUtils().dump()

    return


if __name__ == '__main__':
    main()
