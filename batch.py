#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from module.major_press.yonhapnews import YonhapNewsCrawler
from module.major_press.spotvnews import SpotvNewsCrawler
from module.naver_kin.question_detail import QuestionDetail as NaverKinQuestionDetail
from module.naver_kin.question_list import QuestionList as NaverKinQuestionList
from module.naver_terms.corpus_utils import CorpusUtils as NaverCorpusUtils
from module.naver_terms.detail import TermDetail as NaverTermDetail
from module.naver_terms.term_list import TermList as NaverTermList
from module.twitter.corpus_utils import CorpusUtils as TwitterCorpusUtils
from module.twitter.twitter import TwitterUtils
from module.udemy.udemy import UdemyUtils

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


def init_arguments():
    """ 옵션 설정 """
    import argparse

    parser = argparse.ArgumentParser()

    # 대분류
    parser.add_argument('-udemy', action='store_true', default=False, help='udemy 크롤링')
    parser.add_argument('-twitter', action='store_true', default=False, help='트위터 크롤링')

    parser.add_argument('-naver', action='store_true', default=False, help='네이버')

    parser.add_argument('-major_press', action='store_true', default=False, help='주요 신문사')

    # 백과 사전
    parser.add_argument('-term_list', action='store_true', default=False, help='목록 크롤링')
    parser.add_argument('-term_detail', action='store_true', default=False, help='본문 크롤링')

    # 주요 신문사
    parser.add_argument('-yonhapnews', action='store_true', default=False, help='연합뉴스')
    parser.add_argument('-spotvnews', action='store_true', default=False, help='스포티비뉴스')

    # 지식인
    parser.add_argument('-kin_question_list', action='store_true', default=False,
                        help='질문 목록 크롤링')
    parser.add_argument('-kin_detail', action='store_true', default=False,
                        help='답변 상세 페이지 크롤링')

    # 지식인 질문 상세 페이지: elasticsearch 파라메터
    parser.add_argument('-index', default='question_list', help='인덱스명')
    parser.add_argument('-match_phrase', default='{"fullDirNamePath": "주식"}', help='검색 조건')

    # 데이터 덤프
    parser.add_argument('-dump', action='store_true', default=False, help='크롤링 결과 덤프')

    # 실행 모드 데몬/배치
    parser.add_argument('-batch', action='store_true', default=False, help='데몬으로 실행')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    # 주요 신문사
    if args.major_press:
        if args.yonhapnews:
            YonhapNewsCrawler().daemon()

        if args.spotvnews:
            SpotvNewsCrawler().daemon()

    # 트위터
    if args.twitter:
        if args.dump:
            TwitterCorpusUtils().dump()
            return

        if args.batch:
            TwitterUtils().batch()
        else:
            TwitterUtils().daemon()

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
            NaverKinQuestionList().daemon()

        if args.kin_detail:
            NaverKinQuestionDetail().batch(list_index=args.index, match_phrase=args.match_phrase)

    return


if __name__ == '__main__':
    main()
