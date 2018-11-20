#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from module.twitter.corpus_utils import CorpusUtils as TwitterCorpusUtils
from module.twitter.twitter import TwitterUtils
from module.udemy.udemy import UdemyUtils

from module.naver_terms.term_list import TermList as NaverTermList
from module.naver_terms.detail import TermDetail as NaverTermDetail
from module.naver_terms.corpus_utils import CorpusUtils as NaverCorpusUtils

from module.naver_kin.question_list import QuestionList as NaverKinQuestionList
from module.naver_kin.question_detail import QuestionDetail as NaverKinQuestionDetail

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
    parser.add_argument('-udemy', action='store_true', default=False, help='udemy 크롤링')
    parser.add_argument('-twitter', action='store_true', default=False, help='트위터 크롤링')

    parser.add_argument('-naver', action='store_true', default=False, help='네이버')

    parser.add_argument('-term_list', action='store_true', default=False, help='목록 크롤링')
    parser.add_argument('-term_detail', action='store_true', default=False, help='본문 크롤링')

    parser.add_argument('-kin_question_list', action='store_true', default=False,
                        help='질문 목록 크롤링')
    parser.add_argument('-kin_detail', action='store_true', default=False,
                        help='답변 상세 페이지 크롤링')

    parser.add_argument('-dump', action='store_true', default=False, help='크롤링 결과 덤프')

    # elasticsearch 파라메터
    parser.add_argument('-index', default='question_list', help='인덱스명')
    parser.add_argument('-match_phrase', default='{"fullDirNamePath": "주식"}', help='검색 조건')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    # 트위터
    if args.twitter:
        if args.dump:
            TwitterCorpusUtils().dump()
            return

        TwitterUtils().batch()

    # udemy
    if args.udemy:
        UdemyUtils().batch()

    # 네이버
    if args.naver:
        if args.term_list:
            NaverTermList().batch()

        if args.term_detail:
            NaverTermDetail().batch()

        if args.dump:
            NaverCorpusUtils().dump()

        if args.kin_question_list:
            NaverKinQuestionList().batch()

        if args.kin_detail:
            NaverKinQuestionDetail().batch(list_index=args.index, match_phrase=args.match_phrase)

    return


if __name__ == '__main__':
    main()
