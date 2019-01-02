#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from module.naver_kin.question_detail import QuestionDetail as NaverKinQuestionDetail
from module.naver_kin.question_list import QuestionList as NaverKinQuestionList
from module.naver_terms.corpus_utils import CorpusUtils as NaverCorpusUtils
from module.naver_terms.detail import TermDetail as NaverTermDetail
from module.naver_terms.term_list import TermList as NaverTermList
from module.twitter.corpus_utils import CorpusUtils as TwitterCorpusUtils
from module.twitter.twitter import TwitterUtils
from module.udemy.udemy import UdemyUtils
from module.web_news import WebNewsCrawler

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


def init_arguments():
    """ 옵션 설정 """
    import argparse

    parser = argparse.ArgumentParser()

    # 작업 아이디
    parser.add_argument('-job_id', default='', help='작업 아이디')

    # 네이버
    parser.add_argument('-naver', action='store_true', default=False, help='네이버')

    # 주요 신문사
    parser.add_argument('-major_press', action='store_true', default=False, help='주요 신문사')

    # 데이터 덤프
    parser.add_argument('-dump', action='store_true', default=False, help='크롤링 결과 덤프')

    # 지식인 질문 상세 페이지: elasticsearch 파라메터, job_id가 kin_detail일 경우
    parser.add_argument('-index', default='question_list', help='인덱스명')
    parser.add_argument('-match_phrase', default='{"fullDirNamePath": "주식"}', help='검색 조건')

    # 실행 모드 데몬/배치
    parser.add_argument('-batch', action='store_true', default=False, help='배치 모드로 실행')

    parser.add_argument('-producer', action='store_true', default=False, help='mq producer test')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    # 네이버
    if args.naver:
        if args.job_id == 'term_list':
            NaverTermList().batch()

        if args.job_id == 'term_detail':
            NaverTermDetail().batch()

        if args.job_id == 'dump':
            NaverCorpusUtils().dump()

        if args.job_id == 'kin_question_list':
            NaverKinQuestionList().daemon()

        if args.job_id == 'kin_detail':
            NaverKinQuestionDetail().batch(list_index=args.index, match_phrase=args.match_phrase)

    # 주요 신문사
    if args.job_id:
        # 트위터
        if args.job_id == 'twitter':
            if args.dump:
                TwitterCorpusUtils().dump()
                return

            if args.batch:
                TwitterUtils().batch()
            else:
                TwitterUtils().daemon()

        # udemy
        if args.job_id == 'udemy':
            UdemyUtils().batch()

        if args.batch:
            WebNewsCrawler(job_id=args.job_id, column='trace_list').batch()
        else:
            WebNewsCrawler(job_id=args.job_id, column='trace_list').daemon()

    if args.producer:
        from module.producer import MqProducerUtils

        MqProducerUtils().batch()

    return


if __name__ == '__main__':
    main()
