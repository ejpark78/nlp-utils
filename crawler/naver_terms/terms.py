#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from crawler.naver_terms.detail import TermsDetail as NaverTermsDetail
from crawler.naver_terms.list import TermsList as NaverTermsList


class TermsCrawler(object):
    """백과사전 크롤링"""

    def __init__(self):
        super().__init__()

    def batch(self):
        params = self.init_arguments()

        if params['list'] is True:
            NaverTermsList(params=params).batch()
            return
        elif params['detail'] is True:
            NaverTermsDetail(params=params).batch()
            return

        return

    @staticmethod
    def init_arguments() -> dict:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--config', default=None, type=str, help='설정 파일 정보')

        parser.add_argument('--list', action='store_true', default=False, help='목록')
        parser.add_argument('--detail', action='store_true', default=False, help='상세 정보')

        parser.add_argument('--sub-category', default='', help='하위 카테고리')

        parser.add_argument('--sleep', default=10, type=float, help='sleep time')

        return vars(parser.parse_args())


if __name__ == '__main__':
    TermsCrawler().batch()
