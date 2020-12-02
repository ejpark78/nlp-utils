#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
from time import sleep
from urllib.parse import urljoin

import pytz
import urllib3
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.rrule import rrule, WEEKLY, MO

from module.movie_reviews.daum.base import DaumMovieBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DaumMovieCode(DaumMovieBase):

    def __init__(self, params):
        super().__init__(params=params)

    def save_movie_code(self, url, content, meta):
        soup = BeautifulSoup(content, 'html5lib')

        buf = set()
        for item in soup.select('ul.list_movie li div.info_tit a'):
            if item.get_text() == '':
                continue

            if item['href'].find('movieId') < 0:
                continue

            values = (
                urljoin(url, item['href']),
                re.sub(r'^.+movieId=(\d+).*$', r'\g<1>', item['href']),
                item.contents[-1],
            )

            buf.add(values[1])

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '영화 코드 저장',
                'code': values[1],
                'title': values[2],
                **meta
            })

            try:
                self.db.cursor.execute(self.db.template['code'], values)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '영화 코드 저장 오류',
                    'code': values[1],
                    'title': values[2],
                    'error': str(e),
                    **meta
                })

        self.db.conn.commit()

        return ','.join(list(buf))

    def batch(self):
        timezone = pytz.timezone('Asia/Seoul')

        dt_list = sorted(list(
            rrule(
                freq=WEEKLY,
                byweekday=MO,
                dtstart=parse_date('2004-01-01').astimezone(self.timezone),
                until=parse_date('2020-10-27').astimezone(timezone)
            )), reverse=True)

        for dt in dt_list:
            url = self.url['code'].format(year=dt.year, month=dt.month, day=dt.day)

            contents = self.db.read_cache(url=url, meta={})
            _ = self.save_movie_code(url=url, content=contents['content'], meta={})

            if contents['is_cache'] is False:
                sleep(self.params.sleep)

        return
