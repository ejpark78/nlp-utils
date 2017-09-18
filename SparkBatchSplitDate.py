#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import json

from pyspark import SparkContext, SparkConf


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


def map_function(line):
    """
    개별 excutor 에서 실행되는 작업
    """
    import dateutil.parser

    document = json.loads(line)

    # 날짜 변환
    date = None
    if 'date' in document:
        if '$date' in document['date']:
            document['date'] = document['date']['$date']
        elif 'date' in document['date']:
            document['date'] = document['date']['date']

        date = dateutil.parser.parse(document['date'])
        line = json.dumps(document, ensure_ascii=False, sort_keys=True)

    return date.strftime('%Y-%m'), line


def month_partitioner(month):
    return hash(month)


def parse_argument():
    """"
    옵션 입력
    """
    import argparse

    arg_parser = argparse.ArgumentParser(description='')

    arg_parser.add_argument('-filename', help='filename', default='corpus/sample.json.bz2')
    arg_parser.add_argument('-result', help='result tag ', default='2017')

    return arg_parser.parse_args()


if __name__ == "__main__":
    conf = SparkConf()
    sc = SparkContext(appName='batch', conf=conf)

    args = parse_argument()

    # print('applicationId:', sc.applicationId, flush=True)

    rdd = sc.textFile(args.filename)\
        .map(lambda x: map_function(x))

    # month = rdd.filter(lambda k,v: k == '2017-02')
    # month.saveAsTextFile('2017-02')

    mapping = sc.broadcast(
        rdd.keys().  # Get keys
            distinct().  # Find unique
            sortBy(lambda x: x).  # Sort
            zipWithIndex().  # Add index
            collectAsMap())

    # print('mapping: ', mapping, flush=True)

    rdd.partitionBy(
        len(mapping.value),
        partitionFunc=lambda x: mapping.value.get(x)
        ).values().saveAsTextFile(args.result)

    # .partitionBy(12, month_partitioner)
    # 저장
    # from tempfile import NamedTemporaryFile
    #
    # tempFile = NamedTemporaryFile(delete=True)
    # tempFile.close()
    #
    # rdd.values().saveAsTextFile(tempFile.name)
    #
    # print(tempFile.name)

    # rdd.mapPartitions(lambda x: map_by_month(x)) \
    #     .collect()


    # import bz2
    # fp_list = {}
    #
    # count = 0
    # for line in result:
    #     date = line[0]
    #     if date not in fp_list:
    #         fp_list[date] = bz2.open('{}/{}.json.bz2'.format(args.result_dir, date), 'wt')
    #
    #     fp_list[date].write(line[1] + '\n')
    #
    #     count += 1
    #     if count % 10000 == 0:
    #         fp_list[date].flush()
    #
    #
    # for date in fp_list:
    #     fp_list[date].close()
