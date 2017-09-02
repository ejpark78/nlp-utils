#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import pycrfsuite

from CRFFeature import CRFFeature


class NCNamedEntityTagger:
    """
    개체명 인식기
    """
    def __init__(self, filename=None):
        self.tagger = None

        if filename is not None:
            self.open(filename)

    def open(self, filename):
        """
        crf 모델 오픈
        """
        if self.tagger is not None:
            self.tagger.close()

        self.tagger = pycrfsuite.Tagger()
        self.tagger.open(filename)

    @staticmethod
    def _to_xml(raw_sentence, ne_info=None):
        """
        CRF 태깅 결과를 텍스트 형태로 반환

            {'BI_TAG': 'B', 'WORD': 루, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 크, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'B', 'WORD': 스, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 캇, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 이, 'NE_TAG': O}

            {'BI_TAG': 'B', 'WORD': 루크 스캇, 'NE_TAG': PERSON_PIT}
            {'BI_TAG': 'I', 'WORD': 이, 'NE_TAG': O}

            <NE L1="PERSON" L2="PIT">루크 스캇</NE>이
        """
        prev = ''
        buf = []
        for token in raw_sentence:
            if token['NE_TAG'] != 'O' and token['NE_TAG'] == prev:
                if token['BI_TAG'] == 'B':
                    buf[len(buf)-1]['WORD'] += ' ' + token['WORD']
                else:
                    buf[len(buf)-1]['WORD'] += token['WORD']

                prev = token['NE_TAG']
                continue

            prev = token['NE_TAG']
            buf.append(token)

        buf_sentence = []
        for token in buf:
            if token['BI_TAG'] == 'B':
                buf_sentence.append(' ')

            if token['NE_TAG'] == 'O':
                buf_sentence.append(token['WORD'])
            else:
                l1, l2 = token['NE_TAG'].split('_')
                buf_sentence.append('<NE L1="{}" L2="{}">{}</NE>'.format(l1, l2, token['WORD']))

                if ne_info is not None:
                    if l1 not in ne_info:
                        ne_info[l1] = {}

                    if token['WORD'] not in ne_info[l1]:
                        ne_info[l1][token['WORD']] = 0

                    ne_info[l1][token['WORD']] += 1

        return "".join(buf_sentence)

    def tag(self, sentence, ne_info=None):
        """
        하나의 문장을 태깅
        """
        feature = CRFFeature()

        # 띄어 쓰기 자질 (BI) 태그
        bi_tagged = feature.tag_space(sentence.strip())

        # 자질 추출
        x_test = feature.sentence2features(bi_tagged)

        # CRF 태깅
        crf_result = self.tagger.tag(x_test)

        # 중간 결과 취합
        tagging_result = feature.merge_tagging_result(bi_tagged, crf_result)

        return self._to_xml(tagging_result, ne_info)

    @staticmethod
    def parse_argument():
        """
        프로그램 실행 인자 설정
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='개체명 인식기')

        # run tagger
        arg_parser.add_argument('-stdin', help='표준 입력으로 태깅', action='store_true', default=False)

        arg_parser.add_argument('-filename', type=str, help='모델 파일명', default='model/baseball-all.model')

        return arg_parser.parse_args()


if __name__ == '__main__':
    tagger = NCNamedEntityTagger()
    args = tagger.parse_argument()

    # load model
    tagger.open(args.filename)

    for line in sys.stdin:
        line = line.strip()
        tagged = tagger.tag(line)

        print('{}\t{}'.format(line, tagged))
