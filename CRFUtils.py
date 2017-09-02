#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import bz2
import json


class CRFUtils:
    """
    CRF 자질 추출 및 학습에 필요한 유틸
    """
    def __init__(self):
        pass

    def sec2time(self, sec, n_msec=0):
        """
        초를 시간 문자열로 변환후 반환
        """
        if hasattr(sec, '__len__'):
            return [self.sec2time(s) for s in sec]

        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        if n_msec > 0:
            pattern = '%%02d:%%02d:%%0%d.%df' % (n_msec + 3, n_msec)
        else:
            pattern = r'%02d:%02d:%02d'

        if d == 0:
            return pattern % (h, m, s)

        return ('%d days, ' + pattern) % (d, h, m, s)

    def parse_xml_format(self, ne_tagged):
        """
        NE xml 형식을 변환

        입력:
            ESPN <QuotID=1>은 <NE L1="PERSON" L2="PIT">류현진</NE>이 체인지업 외에도 또 하나의 <QuotID=2>을 지니게 됐다.
        출력:
            [{'WORD': ESPN}]
            [{'WORD': <QuotId=1>}, {'WORD': 은}]
            [{'WORD': 류현진, 'L1': 'PERSON', 'L2': 'PIT'}, {'WORD': 이}]
            [{'WORD': 체인지업}]
            ...
        """
        token_list = self.split_xml_sentence(ne_tagged)

        # "ESPN",
        # "<QuotID=1>",
        # "<NE L1=\"PERSON\" L2=\"PIT\">류현진</NE>이",
        # "체인지업",

        result = []
        for token in token_list:
            buf = []

            m = re.search(r'^(.*)<NE L1="(.+)" L2="(.+)">(.+)</NE>(.*)$', token)
            if m is not None:
                # "<NE L1=\"PERSON\" L2=\"PIT\">류현진</NE>이",

                if m.group(1) != '':
                    buf.append({'WORD': m.group(1)})

                buf.append({'WORD': m.group(4), 'L1': m.group(2), 'L2': m.group(3)})

                if m.group(5) is not None and m.group(5) != '':
                    buf.append({'WORD': m.group(5)})

                result.append(buf)
                continue
            else:
                m = re.search(r'^(.*)<NE L1="(.+)">(.+)</NE>(.*)$', token)
                if m is not None:
                    # "<NE L1=\"PERSON\">류현진</NE>이",

                    if m.group(1) != '':
                        buf.append({'WORD': m.group(1)})

                    buf.append({'WORD': m.group(3), 'L1': m.group(2)})

                    if m.group(4) is not None and m.group(4) != '':
                        buf.append({'WORD': m.group(4)})

                    result.append(buf)
                    continue

            m = re.search(r'^(.*)(<quotid=\d+>)(.*)$', token, re.IGNORECASE)
            if m is not None:
                # <QuotID=1>은

                if m.group(1) != '':
                    buf.append({'WORD': m.group(1)})

                buf.append({'WORD': m.group(2).upper()})

                if m.group(3) is not None and m.group(3) != '':
                    buf.append({'WORD': m.group(3)})

                result.append(buf)
                continue

            buf.append({'WORD': token})
            result.append(buf)

        return result

    @staticmethod
    def split_xml_sentence(ne_tagged):
        """
        입력문장을 어절 단위로 분리
        """
        result = []

        tag_start = False
        for token in ne_tagged.split(' '):
            if tag_start is True:
                result[len(result) - 1] += ' ' + token
            else:
                result.append(token)

            if token == '<NE':
                tag_start = True
            elif token.find('</NE>') > 0:
                tag_start = False

        return result

    @staticmethod
    def split_ne_tag(ne_tagged):
        """
        NE tag 분리

        입력:
            ESPN <QuotID=1> <NE L1="PERSON" L2="PIT">류현진</NE>이 체인지업 외에도 또 하나의 <QuotID=2>을 지니게 됐다.

            [
                [{'WORD': <QuotID=1>}]
                [{'WORD': 류현진, 'L1': 'PERSON', 'L2': 'PIT'}, {'WORD': 이}]
            ]
        출력:
            [
                {'BI_TAG': 'B', 'WORD': <QuotID=1>, 'NE_TAG':O}

                {'BI_TAG': 'B', 'WORD': 류, 'NE_TAG': PERSON_PIT}
                {'BI_TAG': 'I', 'WORD': 현, 'NE_TAG': PERSON_PIT}
                {'BI_TAG': 'I', 'WORD': 진, 'NE_TAG': PERSON_PIT}
                {'BI_TAG': 'I', 'WORD': 이, 'NE_TAG': O}
            ]

        """

        result = []
        for word_list in ne_tagged:
            # word_list: [{'WORD': 류현진, 'L1': 'PERSON', 'L2': 'PIT'}, {'WORD': 이}]

            bi_tag = 'B'
            for token in word_list:
                word = token['WORD']

                # ne tag
                ne_tag = 'O'

                # token: [{'WORD': <QuotID=1>}]
                if word.find('QUOTID') > 0:
                    result.append({'BI_TAG': bi_tag, 'WORD': word, 'NE_TAG': ne_tag})
                else:
                    # token: {'WORD': 류현진, 'L1': 'PERSON', 'L2': 'PIT'}

                    if 'L1' in token and 'L2' in token:
                        ne_tag = '{}_{}'.format(token['L1'], token['L2'])

                    i = 0
                    while i < len(word):
                        result.append({'BI_TAG': bi_tag, 'WORD': word[i], 'NE_TAG': ne_tag})
                        bi_tag = 'I'
                        i += 1

        return result

    def read_corpus(self, filename):
        """
        학습셋 말뭉치 디비에서 학습셋을 읽음.
        """
        print('read corpus: {}'.format(filename))

        corpus = []
        with bz2.open(filename, 'r') as fp:
            count = 0
            for line in fp:
                document = json.loads(str(line,'utf-8'))

                if 'named_entity' not in document:
                    document['named_entity'] = {
                        'xml': document['ne_tagged'],
                        'parsed': self.parse_xml_format(document['ne_tagged'])
                    }
                    del document['ne_tagged']

                bi_tagged = self.split_ne_tag(document['named_entity']['parsed'])
                corpus.append(bi_tagged)

                count += 1
                if count % 1000 == 0:
                    print('.', end='', flush=True)

        print('\n', flush=True)
        print('corpus size: {:,}'.format(len(corpus)), flush=True)

        return corpus

    @staticmethod
    def save_corpus(filename, corpus):
        """
        학습셋 말뭉치 저장
        """
        print('save corpus: {}'.format(filename))

        with open(filename+'.new.json', 'w', encoding='utf-8') as fp:
            count = 0
            for document in corpus:
                line = json.dumps(document, ensure_ascii=False, sort_keys=True)
                fp.write(line+'\n')

                count += 1
                if count % 1000 == 0:
                    fp.flush()

                if count % 1000 == 0:
                    print('.', end='', flush=True)

            fp.flush()

        print('\n', flush=True)
        print('corpus size: {:,}'.format(len(corpus)), flush=True)

        return corpus


if __name__ == '__main__':
    pass
