#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys

from module.web_news_test import WebNewsCrawlerTest

MESSAGE = 25

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(format='%(message)s')

root_logger = logging.getLogger()

root_logger.setLevel(MESSAGE)
root_logger.handlers = [logging.StreamHandler(sys.stderr)]


def init_arguments():
    """ 옵션 설정 """
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('-test', action='store_true', default=False, help='테스트')

    # 작업 아이디
    parser.add_argument('-category', default='', help='작업 카테고리')
    parser.add_argument('-job_id', default='', help='작업 아이디')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    # 디버깅 테스트
    if args.test:
        WebNewsCrawlerTest(
            category=args.category,
            job_id=args.job_id,
            column='trace_list'
        ).test()

        return

    return


if __name__ == '__main__':
    main()
