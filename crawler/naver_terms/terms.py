#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os import getenv

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

        parser.add_argument('--config', default=getenv('CRAWLER_CONFIG', default=None), type=str, help='설정 파일 정보')

        parser.add_argument('--list', action='store_true', default=False, help='목록')
        parser.add_argument('--detail', action='store_true', default=False, help='상세 정보')

        parser.add_argument('--sub-category', default=getenv('CRAWLER_SUBCATEGORY', default=''), help='하위 카테고리')

        parser.add_argument('--host', default=getenv('ELASTIC_SEARCH_HOST', default=None), type=str,
                            help='elasticsearch url')
        parser.add_argument('--index', default=getenv('ELASTIC_SEARCH_INDEX', default=None), type=str,
                            help='elasticsearch index')
        parser.add_argument('--list-index', default=getenv('ELASTIC_SEARCH_LIST_INDEX', default=None), type=str,
                            help='elasticsearch list index')
        parser.add_argument('--auth-encoded', default=getenv('ELASTIC_SEARCH_AUTH_ENCODED', default=None), type=str,
                            help='elasticsearch auth')

        parser.add_argument('--sleep', default=getenv('CRAWLER_SLEEP', default=None), type=float, help='sleep time')

        return vars(parser.parse_args())


if __name__ == '__main__':
    TermsCrawler().batch()
