#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from module.naver.kin.question_detail import QuestionDetail as NaverKinQuestionDetail
from module.naver.kin.question_list import QuestionList as NaverKinQuestionList
from module.naver.kin.user_list import UserList as NaverKinUserList


class NaverKinCrawler(object):
    """네이버 백과사전 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--user-list', action='store_true', default=False)
        parser.add_argument('--question-list', action='store_true', default=False)
        parser.add_argument('--answer-list', action='store_true', default=False)
        parser.add_argument('--question', action='store_true', default=False)
        parser.add_argument('--answer', action='store_true', default=False)

        parser.add_argument('--match_phrase', default='{}', help='검색 조건')
        # parser.add_argument('-match_phrase', default='{"fullDirNamePath": "고민Q&A"}', help='검색 조건')

        parser.add_argument('--sleep', default=10, type=int, help='sleep time')

        return parser.parse_args()

    def batch(self):
        """메인"""
        env = self.init_arguments()

        if env.question_list is True:
            NaverKinQuestionList(sleep_time=env.sleep).batch(column='question')
            return
        elif env.answer_list is True:
            NaverKinQuestionList(sleep_time=env.sleep).batch(column='answer')
            return
        elif env.user_list is True:
            NaverKinUserList(sleep_time=env.sleep).batch()
            return
        elif env.question is True:
            NaverKinQuestionDetail(sleep_time=env.sleep).batch(
                column='question',
                match_phrase=env.match_phrase,
            )
            return
        elif env.answer is True:
            NaverKinQuestionDetail(sleep_time=env.sleep).batch(
                column='answer',
                match_phrase=env.match_phrase,
            )
            return

        return


if __name__ == '__main__':
    NaverKinCrawler().batch()
