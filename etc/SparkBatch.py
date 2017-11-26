#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import json

from pymongo import MongoClient
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
    from dateutil.parser import parse as parse_date

    args = global_args.value

    document = json.loads(line)

    # 날짜 변환
    if 'date' in document:
        if '$date' in document['date']:
            document['date'] = document['date']['$date']
        elif 'date' in document['date']:
            document['date'] = document['date']['date']

        date = parse_date(document['date'])

        collection = date.strftime('%Y-%m')
    else:
        collection = 'error'

    connect = MongoClient('mongodb://{}:{}'.format(args.host, args.port))

    result_db = connect[args.db_name]
    result_db[collection].replace_one({'_id': document['_id']}, document, upsert=True)

    connect.close()

    if 'title' in document:
        print(document['title'])
    else:
        print(document)

    return ''

def parse_argument():
    """"
    옵션 입력
    """
    import argparse

    arg_parser = argparse.ArgumentParser(description='')

    arg_parser.add_argument('-filename', help='filename', default='corpus/news/1st/naver_economy/2017.json.bz2')

    arg_parser.add_argument('-host', help='mongodb host name', default='frodo')
    arg_parser.add_argument('-port', help='mongodb host port', default=37017)
    arg_parser.add_argument('-db_name', help='mongodb name', default='naver_economy')

    return arg_parser.parse_args()


if __name__ == "__main__":
    conf = SparkConf()
    sc = SparkContext(appName='batch', conf=conf)

    args = parse_argument()
    global_args = sc.broadcast(args)

    rdd = sc.textFile(args.filename).map(map_function)
    rdd.collect()

    global_args.unpersist()
    global_args.destroy()
