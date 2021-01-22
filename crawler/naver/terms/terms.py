#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import urllib3
from .detail import TermDetail as NaverTermDetail
from .list import TermList as NaverTermList

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class TermsCrawler(object):
    """백과사전 크롤링"""

    def __init__(self):
        super().__init__()

        self.env = None

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--list', action='store_true', default=False, help='목록')
        parser.add_argument('--detail', action='store_true', default=False, help='상세 정보')

        parser.add_argument('--sub-category', default='', help='하위 카테고리')

        return parser.parse_args()

    def batch(self):
        self.env = self.init_arguments()

        if self.env.list is True:
            NaverTermList().batch(sub_category=self.env.sub_category)
            return
        elif self.env.detail is True:
            NaverTermDetail().batch()
            return

        return


if __name__ == '__main__':
    TermsCrawler().batch()
