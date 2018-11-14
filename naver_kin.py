#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from module.naver_kin.question_list import QuestionList
from module.naver_kin.question_detail import QuestionDetail

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


def init_arguments():
    """ 옵션 설정 """
    import textwrap
    import argparse

    description = textwrap.dedent('''\
# 질문 목록 크롤링
python3 naver_kin_crawler.py -question_list 

# 답변 목록 크롤링 
python3 naver_kin_crawler.py -answer_list \\
    -index partner_list \\
    -match_phrase '{"dirName": "가전제품"}'

# 질문 상세 페이지 크롤링 
python3 naver_kin_crawler.py -detail -index answer_list -match_phrase '{"fullDirNamePath": "주식"}'

python3 naver_kin_crawler.py -detail -index question_list -match_phrase '{"fullDirNamePath": "주식"}'
python3 naver_kin_crawler.py -detail -index question_list -match_phrase '{"fullDirNamePath": "경제 정책"}'
python3 naver_kin_crawler.py -detail -index question_list -match_phrase '{"fullDirNamePath": "경제 동향"}'
python3 naver_kin_crawler.py -detail -index question_list -match_phrase '{"fullDirNamePath": "경제 기관"}'


# 답변 목록을 DB에 저장
python3 naver_kin_crawler.py -insert_answer_list -data_path "data/naver/kin/by_user.economy/(사)한국무역협회"

IFS=$'\\n'
data_path="data/naver/kin/by_user.economy.done"
for d in $(ls -1 ${data_path}) ; do
    echo ${d}

    python3 naver_kin_crawler.py -insert_answer_list \\
        -data_path "${data_path}/${d}"
done

# 데이터 덤프 
python3 naver_kin_crawler.py -dump_elastic_search \\
    -host http://localhost:9200 -index detail \\
    | bzip2 - > detail.detail.json.bz2 

    ''')

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=description)

    # 크롤링
    parser.add_argument('-question_list', action='store_true', default=False,
                        help='질문 목록 크롤링')
    parser.add_argument('-detail', action='store_true', default=False,
                        help='답변 상세 페이지 크롤링')
    parser.add_argument('-answer_list', action='store_true', default=False,
                        help='답변 목록 크롤링 (전문가 답변, 지식 파트너 답변 등)')

    parser.add_argument('-elite_user_list', action='store_true', default=False,
                        help='전문가 목록 크롤링')
    parser.add_argument('-rank_user_list', action='store_true', default=False,
                        help='랭킹 사용자 목록 크롤링')
    parser.add_argument('-partner_list', action='store_true', default=False,
                        help='지식 파트너 목록 크롤링')
    parser.add_argument('-get_expert_list', action='store_true', default=False,
                        help='전문가 목록 크롤링')

    # 결과 덤프
    parser.add_argument('-export_detail', action='store_true', default=False,
                        help='export_detail')
    parser.add_argument('-dump_elastic_search', action='store_true', default=False,
                        help='데이터 덤프')

    parser.add_argument('-sync_id', action='store_true', default=False,
                        help='')

    # 파라메터
    parser.add_argument('-host', default='http://localhost:9200', help='elastic-search 주소')
    parser.add_argument('-index', default='question_list', help='인덱스명')
    parser.add_argument('-match_phrase', default='{"fullDirNamePath": "주식"}', help='검색 조건')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    if args.question_list:
        QuestionList().batch()

    if args.detail:
        QuestionDetail().get_detail(index=args.index, match_phrase=args.match_phrase)

    # # 사용자 목록 크롤링
    # if args.elite_user_list:
    #     crawler.get_elite_user_list()
    #
    # if args.rank_user_list:
    #     crawler.get_rank_user_list()
    #
    # if args.partner_list:
    #     crawler.get_partner_list()
    #
    # if args.get_expert_list:
    #     crawler.get_expert_list()
    #
    # # 데이터 추출
    # if args.dump_elastic_search:
    #     crawler.dump_elastic_search(host=args.host, index=args.index)
    #
    # if args.export_detail:
    #     crawler.export_detail()
    #
    # if args.sync_id:
    #     crawler.sync_id(index=args.index)

    return


if __name__ == '__main__':
    main()
