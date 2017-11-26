#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import json

from pyspark import SparkContext, SparkConf


def map_function(line):
    """
    개별 excutor 에서 실행되는 작업
    """
    from dateutil.parser import parse as parse_date

    document = json.loads(line)

    # 날짜 변환
    date = None
    if 'date' in document:
        if '$date' in document['date']:
            document['date'] = document['date']['$date']
        elif 'date' in document['date']:
            document['date'] = document['date']['date']

        date = parse_date(document['date'])
        line = json.dumps(document, ensure_ascii=False, sort_keys=True)

    return date.strftime('%Y-%m-%d %H:%M:%S'), line


def parse_argument():
    """"
    옵션 입력
    """
    import argparse

    arg_parser = argparse.ArgumentParser(description='')

    arg_parser.add_argument('-filename', help='filename', default='corpus/news/1st/naver_economy/2017.json.bz2')
    arg_parser.add_argument('-result', help='result', default='date/result.json.bz2')

    return arg_parser.parse_args()


if __name__ == "__main__":
    conf = SparkConf()
    sc = SparkContext(appName='batch', conf=conf)

    args = parse_argument()

    result = sc.textFile(args.filename).map(lambda line: map_function(line)).sortByKey().collect()

    import bz2
    with bz2.open('{}'.format(args.result), 'wt') as fp:
        count = 0
        for token in result:
            fp.write(token[1]+'\n')

            if count % 1000:
                fp.flush()

        fp.flush()

    # from tempfile import NamedTemporaryFile
    #
    # tempFile = NamedTemporaryFile(delete=True)
    # tempFile.close()
    #
    # rdd.values().saveAsTextFile(tempFile.name)
    #
    # print(tempFile.name)


