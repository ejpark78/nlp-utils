#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from module.elasticsearch_utils import ElasticSearchUtils
from module.naver_kin.question_detail import QuestionDetail as NaverKinQuestionDetail
from module.naver_kin.question_list import QuestionList as NaverKinQuestionList
from module.naver_terms.corpus_utils import CorpusUtils as NaverCorpusUtils
from module.naver_terms.detail import TermDetail as NaverTermDetail
from module.naver_terms.term_list import TermList as NaverTermList
from module.twitter.corpus_utils import CorpusUtils as TwitterCorpusUtils
from module.twitter.twitter import TwitterUtils
from module.udemy.udemy import UdemyUtils
from module.web_news import WebNewsCrawler

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=MESSAGE)


def init_arguments():
    """ 옵션 설정 """
    import argparse

    parser = argparse.ArgumentParser()

    # 작업 아이디
    parser.add_argument('-job_category', default='', help='작업 카테고리')
    parser.add_argument('-job_id', default='', help='작업 아이디')

    # 데이터 덤프
    parser.add_argument('-dump', action='store_true', default=False, help='크롤링 결과 덤프')

    # 지식인 질문 상세 페이지: elasticsearch 파라메터, job_id가 kin_detail일 경우
    parser.add_argument('-host', default=None, help='호스트')
    parser.add_argument('-index', default='question_list', help='인덱스명')
    parser.add_argument('-match_phrase', default='{"fullDirNamePath": "주식"}', help='검색 조건')

    # 실행 모드 데몬/배치
    parser.add_argument('-batch', action='store_true', default=False, help='배치 모드로 실행')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    # 네이버 지식인/백과사전
    if args.job_category == 'naver':
        if args.job_id == 'term_list':
            NaverTermList().batch()
            return

        if args.job_id == 'term_detail':
            NaverTermDetail().batch()
            return

        if args.job_id == 'dump':
            NaverCorpusUtils().dump()
            return

        if args.job_id == 'kin_question_list':
            NaverKinQuestionList().daemon()
            return

        if args.job_id == 'kin_detail':
            NaverKinQuestionDetail().batch(list_index=args.index, match_phrase=args.match_phrase)
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

    # elasticsearch 배치 작업
    if args.batch:
        ElasticSearchUtils(host=args.host, index=args.index).batch()
        return

    if args.batch:
        WebNewsCrawler(job_category=args.job_category, job_id=args.job_id, column='trace_list').batch()
        return
    else:
        WebNewsCrawler(job_category=args.job_category, job_id=args.job_id, column='trace_list').daemon()
        return


if __name__ == '__main__':
    main()
