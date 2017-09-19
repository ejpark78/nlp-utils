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
    import re
    import dateutil.parser
    from urllib.parse import urlparse, parse_qs

    document = json.loads(line)

    # document id 변경
    url = get_url(document['url'])
    if url.find('naver') > 0 and document['_id'].find('naver') > 0:
        document_id_format = '{oid}-{aid}'
        simple_url_format = 'oid={oid}&aid={aid}'

        url_info = urlparse(url)
        url_query = parse_qs(url_info.query)
        for key in url_query:
            url_query[key] = url_query[key][0]

        document['_id'] = document_id_format.format(**url_query)
        if isinstance(document['url'], str):
            url_base = '{}://{}{}'.format(url_info.scheme, url_info.netloc, url_info.path)
            document['url'] = {
                'full': url,
                'simple': '{}?{}'.format(url_base, simple_url_format.format(**url_query)),
                'query': url_query
            }

    if url.find('nate') > 0 or url.find('daum') > 0:
        url_info = urlparse(url)

        document_id = url

        document_id = document_id.replace('{}://{}'.format(url_info.scheme, url_info.hostname), '')
        document_id = document_id.replace('/view/', '')
        document_id = document_id.replace('/v/', '')
        document_id = re.sub('\?mid=.+$', '', document_id)

        document['_id'] = document_id

        document['url'] = {
            'full': url
        }

    # 날짜 변환
    date = None
    if 'date' in document:
        date = None
        if '$date' in document['date']:
            date = document['date']['$date']
        elif 'date' in document['date']:
            date = document['date']['date']

        if date is not None:
            date = dateutil.parser.parse(date)

    # 변경된 값 반영
    line = json.dumps(document, ensure_ascii=False, sort_keys=True)

    group = 'error'
    if date is not None:
        group = date.strftime('%Y-%m')

    return group, line


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

    print('applicationId: ', sc.applicationId, flush=True)

    args = parse_argument()

    rdd = sc.textFile(args.filename)\
        .map(lambda x: map_function(x))

    mapping = sc.broadcast(
        rdd.keys()
            .distinct()
            .sortBy(lambda x: x)
            .zipWithIndex()
            .collectAsMap()
    )

    rdd.partitionBy(
            len(mapping.value),
            partitionFunc=lambda x: mapping.value.get(x)
        )\
        .values()\
        .saveAsTextFile(
            args.result,
            compressionCodecClass="org.apache.hadoop.io.compress.BZip2Codec"
        )

    # print(mapping.value, flush=True)

    # pip3 install hdfs, webhdfs 사용
    from hdfs import TokenClient

    client = TokenClient('http://master:50070', None, root='/user/ejpark')

    for tag in mapping.value:
        src = '{}/part-{:05d}.bz2'.format(args.result, mapping.value[tag])
        dst = '{}/{}.bz2'.format(args.result, tag)

        print(src, dst, flush=True)
        client.rename(src, dst)


    # import pyarrow as pa
    #
    # hdfs_fs = pa.hdfs.connect('master', port=9000)
    # with hdfs_fs.open('{}/mapping.txt'.format(args.result), 'wb') as fp:
    #     fp.write(mapping.value)
    #     fp.flush()

    # by_partition = rdd.partitionBy(
    #         len(mapping.value),
    #         partitionFunc=lambda x: mapping.value.get(x)
    #     )
    #
    # by_partition.foreachPartition(
    #     lambda x: print('x:', x, flush=True)
    # )



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
