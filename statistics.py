#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys
import json

from dateutil.parser import parse as parse_date


def main():
    """
    신문 기사의 통계 정보 추출

    날짜별 문서/문장 수
    월별 문서/문장 수
    년도별 문서/문장 수

    전체 단어수

    :return:
    """
    count = {
        'word': 0,
        'sentence': 0,
        'document': 0,
        'detail': {}
    }

    for line in sys.stdin:
        line = line.strip()
        if line == '':
            continue

        document = json.loads(line)

        dt = None
        if 'date' in document:
            try:
                dt = parse_date(document['date'])
            except Exception as e:
                continue

        if dt is None:
            continue

        if 'paragraph' not in document:
            continue

        paragraph = document['paragraph']

        str_date = dt.strftime('%Y-%m-%d')
        if str_date not in count['detail']:
            count['detail'][str_date] = {
                'word': 0,
                'sentence': 0,
                'document': 0
            }

        detail = count['detail'][str_date]

        count['document'] += 1
        detail['document'] += 1

        for sentence_list in paragraph:
            c = len(sentence_list)
            count['sentence'] += c
            detail['sentence'] += c

            for sentence in sentence_list:
                c = sentence.count(' ') + 1
                count['word'] += c
                detail['word'] += c

        if count['document'] % 1000 == 0:
            print('.', file=sys.stderr, end='', flush=True)
            if count['document'] % 10000 == 0:
                print('({:,})'.format(int(count['document']/1000)), file=sys.stderr, flush=True, end='')

    msg = json.dumps(count, ensure_ascii=False, sort_keys=True, indent=4)
    print('\n', msg, '\n', flush=True)

    return


if __name__ == "__main__":
    main()
