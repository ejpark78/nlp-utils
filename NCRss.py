#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import json

from urllib.parse import urljoin
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import dateutil.parser


import feedparser


def json_serial(obj):
    """
    날자 형식을 문자로 바꾸는 함수
    """
    from datetime import datetime

    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")

    raise TypeError("Type not serializable")


class NCRss:
    """
    뉴스 RSS 크롤링
    """
    def __init__(self):
        pass

    def run(self):
        rss_url = 'http://file.mk.co.kr/news/rss/rss_30100041.xml'

        rss = feedparser.parse(rss_url)
        rss_update_date = dateutil.parser.parse(rss['updated'])
        print('rss_update_date', rss_update_date)

        key_list = {
            'title': 'title',
            'summary': 'summary',
            'published': 'date',
            'author': 'author',
            'no': 'no',
            'link': 'url'
        }

        for item in rss['entries']:
            document = {}
            for key in key_list:
                target = key_list[key]
                document[target] = item[key]

            document['date'] = dateutil.parser.parse(document['date'])

            dump = json.dumps(document, indent=4, ensure_ascii=False, default=json_serial)
            print(dump)

# end of NCRss


if __name__ == '__main__':
    util = NCRss()
    util.run()
    pass

# end of __main__
