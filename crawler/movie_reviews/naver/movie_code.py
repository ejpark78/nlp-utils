#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
from time import sleep
from urllib.parse import urljoin

import urllib3
from bs4 import BeautifulSoup

from crawler.movie_reviews.naver.base import NaverMovieBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class NaverMovieCode(NaverMovieBase):

    def __init__(self, params):
        super().__init__(params=params)

    def save_movie_code(self, url, content, meta):
        soup = BeautifulSoup(content, 'html5lib')

        buf = set()
        for item in soup.select('ul.directory_list li a'):
            if item.get_text() == '':
                continue

            if item['href'].find('code') < 0:
                continue

            values = (
                urljoin(url, item['href']),
                re.sub(r'^.+code=(\d+).*$', r'\g<1>', item['href']),
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
        years = []

        years += [y for y in range(2022, 1990, -1)]
        years += [y for y in range(1980, 1939, -10)]

        prev = ''
        for y in years:
            for p in range(1, 1000):
                url = self.url['code'].format(year=y, page=p)

                contents = self.db.read_cache(url=url, meta={'year': y, 'page': p})
                code_list = self.save_movie_code(url=url, content=contents['content'], meta={'year': y, 'page': p})

                if code_list != '' and prev == code_list:
                    self.logger.log(msg={
                        'level': 'MESSAGE',
                        'message': '중복 목록',
                        'year': y,
                        'page': p,
                    })
                    break

                prev = code_list

                if contents['is_cache'] is False:
                    sleep(self.params.sleep)

        return
