#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from os.path import isfile
from time import sleep

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class AirKoreaCrawler(object):
    """ """

    def __init__(self):
        """ 생성자 """
        super().__init__()

    @staticmethod
    def parse_page(html, filename, day, t):
        soup = BeautifulSoup(html, 'lxml')

        result = []
        for tag in soup.select('dl.forecast'):
            texts = [t.get_text().strip() for t in tag.select('div.txtbox')]

            if len(texts) == 0:
                continue

            item = {
                'day': day,
                'time': t,
                'when': [t.get_text().strip() for t in tag.select('dt')][0],
                'text': texts[0]
            }

            if len(texts) > 1:
                item['reason'] = texts[1]

            result.append(item)

        if filename is None:
            return result

        with open(filename, 'w') as fp:
            fp.write(str(soup))

        return result

    @staticmethod
    def get_html(ymd):
        url = 'http://www.airkorea.or.kr/web/dustForecast?pMENU_NO=113'

        post_data = {
            'loading': 'yes',
            'leftShow': 'realTime',
            'ymd': ymd
        }

        # proxies = {
        #     'http': 'socks5h://127.0.0.1:9150',
        #     'https': 'socks5h://127.0.0.1:9150'
        # }

        resp = requests.post(url, data=post_data, timeout=120)

        return resp.text

    def batch(self):
        """ """
        time_list = '05,11,17,23'.split(',')

        #  2015-12-29
        day_list = [d.strftime('%Y%m%d') for d in pd.date_range(start='2015-12-29', end='2015-12-31')]
        # day_list = [d.strftime('%Y%m%d') for d in pd.date_range(start='2016-01-01', end='2019-12-22')]
        day_list = list(reversed(day_list))

        rows = []

        for day in tqdm(day_list):
            for t in tqdm(time_list, desc=day):
                html = ''

                filename = 'data/airkorea/{day}-{time}.html'.format(day=day, time=t)
                if isfile(filename) is True:
                    with open(filename, 'r') as fp:
                        html = ''.join(fp.readlines())

                    filename = None
                else:
                    try:
                        html = self.get_html(ymd=day + t)
                        sleep(4)
                    except Exception as e:
                        print(e)
                        sleep(4)
                        continue

                rows += self.parse_page(
                    html=html,
                    filename=filename,
                    day=day,
                    t=t,
                )

        df = pd.DataFrame(rows)

        filename = 'data/airkorea-{}~{}.xlsx'.format(df['day'].min(), df['day'].max())
        df.to_excel(filename, index=False)

        return


if __name__ == '__main__':
    utils = AirKoreaCrawler()

    utils.batch()
