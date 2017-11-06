#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import json
import dateutil.parser


def get_url(url):
    """
    url 문자열을 찾아서 반환
    """

    if isinstance(url, str) is True:
        return url
    elif 'simple' in url and url['simple'] != '':
        return url['simple']
    elif 'full' in url:
        return url['full']

    return ''


def extract_date():
    """
    """
    for line in sys.stdin:
        line = line.strip()
        if line == '':
            print(line, flush=True)

        document = json.loads(line)

        # 날짜 변환
        date = None
        if 'date' in document:
            if '$date' in document['date']:
                document['date'] = document['date']['$date']
            elif 'date' in document['date']:
                document['date'] = document['date']['date']

            date = dateutil.parser.parse(document['date'])

        url = get_url(document['url'])

        print('{}\t{}\t{}\t{}'.format(date.strftime('%Y-%m-%d'), url, date.strftime('%Y-%m-%d %H:%M:%S'), line))

    return


def split_by_month(result_dir):
    """
    """

    import bz2

    fp_list = {}

    count = 0
    for line in sys.stdin:
        line = line.strip()
        if line == '':
            print(line, flush=True)
            continue

        token = line.split('\t')

        fname = token[0]
        # url = token[1]
        # date = token[2]
        str_document = token[3]

        if fname not in fp_list:
            fp_list[fname] = bz2.open('{}/{}.json.bz2'.format(result_dir, fname), 'wt')

        fp_list[fname].write(str_document + '\n')

        count += 1
        if count % 1000 == 0:
            print('.', end='', flush=True)
            fp_list[fname].flush()

    for fname in fp_list:
        fp_list[fname].flush()
        fp_list[fname].close()

    return


def parse_argument():
    """"
    옵션 입력
    """
    import argparse

    arg_parser = argparse.ArgumentParser(description='')

    arg_parser.add_argument('-extract_date', help='', action='store_true', default=False)
    arg_parser.add_argument('-split_by_month', help='', action='store_true', default=False)

    arg_parser.add_argument('-result_dir', help='result_dir', default='data/result')

    return arg_parser.parse_args()


if __name__ == '__main__':
    args = parse_argument()

    if args.extract_date is True:
        extract_date()
    elif args.split_by_month is True:
        split_by_month(args.result_dir)