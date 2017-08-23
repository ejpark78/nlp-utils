#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import json
import dateutil.parser

import nltk
import csv

from nltk import sent_tokenize
from bs4 import BeautifulSoup

nltk.data.path.append('/home/ejpark/workspace/crawler/resource/nltk_data')


def parse_argument():
    """"
    옵션 설정
    """
    import argparse

    arg_parser = argparse.ArgumentParser(description='')

    arg_parser.add_argument('-tag', help='tag', default='tag')

    return arg_parser.parse_args()


if __name__ == '__main__':
    json_list = {}
    csv_list = {}

    args = parse_argument()

    csv_fp = open('{}.simple.csv'.format(args.tag), 'w')
    csv_writer = csv.writer(csv_fp)

    csv_title = []

    for line in sys.stdin:
        line = line.strip()
        if line == '':
            continue

        if line.find("ISODate(") > 0:
            line = re.sub(r'ISODate\("(.+?)"\)', '"\g<1>"', line)
            
        document = json.loads(line)

        # 필수 컬럼 추출
        result = {}
        for k in ['title', 'date', 'html_content', 'section', 'article_section', '_id']:
            if k in document:
                result[k] = document[k]

        # 날짜 변환
        if 'date' in result:
            if '$date' in result['date']:
                result['date'] = result['date']['$date']

            date = dateutil.parser.parse(result['date'])
            result['date'] = date.strftime('%Y-%m-%d %H:%M:%S')

        # html에서 텍스트 추출
        result['html_content'] = result['html_content'].replace('<br>', '\n')
        result['html_content'] = result['html_content'].replace('<p>', '\n<p>')
        result['html_content'] = result['html_content'].replace('<div>', '\n<div>')
        soup = BeautifulSoup(result['html_content'], 'lxml')

        result['article_text'] = soup.get_text()
        del result['html_content']

        # 문장 분리
        result['sentence_list'] = sent_tokenize(result['article_text'].replace('\n', ' '))
        # for sentence in result['paragraph']:
        #     print(sentence, '\n')

        article_text = result['article_text'].lower()
        title = result['title'].lower()

        str_result = json.dumps(result, sort_keys=True, ensure_ascii=False)

        csv_result = []
        for key in sorted(result):
            if key == 'sentence_list':
                csv_result.append('\n'.join(result[key]))
                continue

            csv_result.append(result[key])

        # csv 타이틀 쓰기
        if len(csv_title) == 0:
            csv_title = sorted(result)
            csv_writer.writerow(csv_title)

        for keyword in ['samsung', 'apple', 'google']:
            if article_text.find(keyword) >= 0 or title.find(keyword) >= 0:
                if keyword not in json_list:
                    json_list[keyword] = open('{}.{}.json'.format(args.tag, keyword), 'w')

                    csv_fp = open('{}.{}.csv'.format(args.tag, keyword), 'w')
                    csv_list[keyword] = csv.writer(csv_fp)

                    csv_list[keyword].writerow(csv_title)

                json_list[keyword].write(str_result+'\n')
                json_list[keyword].flush()

                csv_list[keyword].writerow(csv_result)

        print(str_result, flush=True)

        csv_writer.writerow(csv_result)

    for keyword in json_list:
        json_list[keyword].close()
