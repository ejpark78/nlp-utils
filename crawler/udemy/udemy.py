#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep

import urllib3

from crawler.udemy.course_list import UdemyCourseList
from crawler.udemy.trace_course import UdemyTraceCourse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class UdemyCrawler(object):

    def __init__(self):
        super().__init__()

        self.params = None

    def batch(self):
        """코스 목록 전체를 다운로드한다."""
        self.params = self.init_arguments()

        # if self.params['login'] is True:
        #     UdemyCourseList(params=self.params).selenium.open(url='https://ncsoft.udemy.com')
        #     sleep(10000)

        if self.params['list'] is True:
            UdemyCourseList(params=self.params).batch()

        if self.params['trace'] is True:
            UdemyTraceCourse(params=self.params).batch()

        return

    @staticmethod
    def init_arguments() -> dict:
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--login', action='store_true', default=False)
        parser.add_argument('--headless', action='store_true', default=False)

        parser.add_argument('--list', action='store_true', default=False)
        parser.add_argument('--trace', action='store_true', default=False)

        parser.add_argument('--user-data', default='data/udemy-business/selenium')
        parser.add_argument('--data-path', default='data/udemy-business')

        parser.add_argument('--sleep', default=5, type=float, help='sleep time')
        parser.add_argument('--max-page', default=1, type=int, help='max page')

        return vars(parser.parse_args())


if __name__ == '__main__':
    UdemyCrawler().batch()
