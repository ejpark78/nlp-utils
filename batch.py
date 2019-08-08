#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys

from module.naver_kin.question_detail import QuestionDetail as NaverKinQuestionDetail
from module.naver_kin.question_list import QuestionList as NaverKinQuestionList
from module.naver_kin.user_list import UserList as NaverKinUserList
from module.naver_terms.corpus_utils import CorpusUtils as NaverCorpusUtils
from module.naver_terms.detail import TermDetail as NaverTermDetail
from module.naver_terms.term_list import TermList as NaverTermList
from module.twitter.corpus_utils import CorpusUtils as TwitterCorpusUtils
from module.twitter.twitter import TwitterUtils
from module.udemy.udemy import UdemyUtils
from module.web_news import WebNewsCrawler
from module.web_news_test import WebNewsCrawlerTest
from module.naver_reply import NaverNewsReplyCrawler

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

    parser.add_argument('-test', action='store_true', default=False, help='디버그')

    # 작업 아이디
    parser.add_argument('-category', default='', help='작업 카테고리')
    parser.add_argument('-job_id', default='', help='작업 아이디')

    # 데이터 덤프
    parser.add_argument('-dump', action='store_true', default=False, help='크롤링 결과 덤프')

    # 지식인 질문 상세 페이지: elasticsearch 파라메터, job_id가 kin_detail일 경우
    parser.add_argument('-host', default=None, help='호스트')
    parser.add_argument('-match_phrase', default='{}', help='검색 조건')
    # parser.add_argument('-match_phrase', default='{"fullDirNamePath": "고민Q&A"}', help='검색 조건')

    # 실행 모드 데몬/배치
    parser.add_argument('-batch', action='store_true', default=False, help='배치 모드로 실행')

    # 재크롤링
    parser.add_argument('-re_crawl', action='store_true', default=False, help='전체를 다시 크롤링')

    parser.add_argument('-query', default='', help='elasticsearch query')
    parser.add_argument('-query_field', default='date', help='query field')

    parser.add_argument('-date_range', default=None, help='date 날짜 범위: 2000-01-01~2019-04-10')
    parser.add_argument('-date_step', default=-1, type=int, help='date step')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    # 네이버 지식인/백과사전
    if args.category == 'naver':
        if args.job_id == 'sports-reply':
            NaverNewsReplyCrawler(
                category=args.category,
                job_id=args.job_id,
                column='trace_list'
            ).batch(date_range=args.date_range)
            return

        if args.job_id == 'term_list':
            NaverTermList().batch()
            return
        elif args.job_id == 'term_detail':
            NaverTermDetail().batch()
            return

        if args.job_id == 'dump':
            NaverCorpusUtils().dump()
            return

        if args.job_id == 'kin_question_list':
            NaverKinQuestionList().daemon(column='question')
            return
        elif args.job_id == 'kin_answer_list':
            NaverKinQuestionList().daemon(column='answer')
            return
        elif args.job_id == 'kin_user_list':
            NaverKinUserList().daemon()
            return
        elif args.job_id == 'kin_detail_question':
            NaverKinQuestionDetail().daemon(
                column='question',
                match_phrase=args.match_phrase,
            )
            return
        elif args.job_id == 'kin_detail_answer':
            NaverKinQuestionDetail().daemon(
                column='answer',
                match_phrase=args.match_phrase,
            )
            return

    # 트위터
    if args.job_id == 'twitter':
        if args.dump:
            TwitterCorpusUtils().dump()
            return

        if args.batch:
            TwitterUtils().batch()
        else:
            TwitterUtils().daemon()

        return

    # udemy
    if args.job_id == 'udemy':
        UdemyUtils().batch()
        return

    # 디버깅 테스트
    if args.test:
        WebNewsCrawlerTest(
            category=args.category,
            job_id=args.job_id,
            column='trace_list'
        ).test()

        return

    # 재 크롤링: parsing 정보가 변경되었을 경우
    if args.re_crawl:
        WebNewsCrawlerTest(
            category=args.category,
            job_id=args.job_id,
            column='trace_list'
        ).re_crawl(
            query=args.query,
            date_range=args.date_range,
            query_field=args.query_field,
        )
        return

    # 웹 신문
    if args.batch:
        WebNewsCrawler(
            category=args.category,
            job_id=args.job_id,
            column='trace_list',
            date_step=args.date_step,
            date_range=args.date_range,
        ).batch()
    else:
        WebNewsCrawler(
            category=args.category,
            job_id=args.job_id,
            column='trace_list',
            date_step=args.date_step,
            date_range=args.date_range,
        ).daemon()

    return


if __name__ == '__main__':
    main()
