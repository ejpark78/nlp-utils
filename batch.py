#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys


def init_arguments():
    """
    옵션 설정

    :return:
    """
    import argparse

    parser = argparse.ArgumentParser(description='batch')

    parser.add_argument('-batch', help='', action='store_true', default=True)

    return parser.parse_args()


def main():
    import re
    from language_utils.language_utils import LanguageUtils

    # 사전 경로 지정
    dictionary_path = 'language_utils/dictionary'

    util = LanguageUtils()

    # 사전 오픈
    util.open(engine='sp_utils/pos_tagger', path='{}/rsc'.format(dictionary_path))

    # "B"=야구 "E"=경제 "T"=야구 용어
    util.open(engine='sp_utils/ne_tagger', config='sp_config.ini', domain='B')
    util.open(engine='sp_utils/ne_tagger', config='sp_config.ini', domain='T')

    # fp = open('data/speech_requests/4. 나무 위키/test', 'r')
    # for line in fp.readlines():

    for line in sys.stdin:
        line = line.strip()
        if line == '':
            continue

        if 'http' in line:
            continue

        line = re.sub(r"'''(.*?)'''", '\g<1>', line)

        count = 0
        try:
            # 문장 분리
            sentence_list = util.run_sentence(engine='split_sentence', paragraph=line)

            for sentence in sentence_list:
                clean_sentence = re.sub(r'\[\[.+?\]\]', '', sentence)

                # 형태소 분석 실행
                pos_tagged = util.run_sentence(engine='sp_utils/pos_tagger', sentence=clean_sentence)[0]

                # 사전 기반 개체명 인식 실행
                sp_named_entity = util.run_sentence(engine='sp_utils/ne_tagger',
                                                    sentence=clean_sentence, pos_tagged=pos_tagged)

                word_list = re.findall(r'\[\[(.+?)\]\]', sentence)

                print('{}\t{}\t{}\t{}\t{}\t{}'.format(
                    clean_sentence, sentence, pos_tagged,
                    sp_named_entity['B'], sp_named_entity['T'], '|'.join(word_list)))
        except Exception as e:
            pass

        count += 1
        if count % 100 == 0:
            print('({:,})'.format(count), file=sys.stderr, flush=True, end='')

    return


def run_convert_mlbpark():
    from crawler.html_parser import HtmlParser

    HtmlParser().convert_mlbpark()


def run_news2csv():
    """

    :return:
    """
    from crawler.utils import Utils

    util = Utils()
    # util.news2csv()
    # util.csv2ellipsis()
    util.news2text()

    return True


if __name__ == "__main__":
    run_convert_mlbpark()
