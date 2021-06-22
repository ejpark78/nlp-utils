#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re

import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class CorpusSizeUtils(object):

    def __init__(self):
        pass

    @staticmethod
    def get_index_size(host: str = 'https://crawler-es.cloud.ncsoft.com:9200', auth: str = 'elastic:searchT2020'):
        """인덱스 크기를 조회한다."""
        url = f'{host}/_cat/indices?v&s=index&h=index,docs.count'

        resp = requests.get(
            url=url,
            auth=tuple(auth.split(':')),
            verify=False,
        )

        alias = {
            'sports-reply': 'sports_reply'
        }

        index = {'total': 0}
        for l in resp.text.split('\n')[1:]:
            if l == '' or l[0] == '.':
                continue

            for src in alias:
                l = l.replace(src, alias[src])

            # 사이즈 분리
            i_name, count = re.sub(
                r'crawler-(.+?)\s+(\d+)$',
                r'\g<1>\t\g<2>',
                l,
            ).split('\t', maxsplit=1)

            if count.isdecimal():
                count = int(count)

            if count == 0:
                continue

            # 인덱스명 파싱: site - category - year
            t = i_name.split('-')

            year = ''

            # 년도
            if t[-1].isdecimal():
                year = t[-1]
                t.pop()

            site = t[0]
            t = t[1:]

            category = '_'.join(t)

            index['total'] += count

            if site not in index:
                index[site] = {}

            if category not in index[site]:
                index[site][category] = {}

            if year != '':
                if year not in index[site][category]:
                    index[site][category][year] = 0

                index[site][category][year] += count
            else:
                category = '-'.join([site, category])

                if 'etc' not in index:
                    index['etc'] = {}

                if category not in index['etc']:
                    index['etc'][category] = 0

                index['etc'][category] += count

        return index

    @staticmethod
    def add_sum_column(data):
        """합계 컬럼을 넣는다."""
        df = pd.DataFrame(data).fillna(0)

        df.index.name = 'year'

        df['합계'] = df.sum(axis=1)
        df.loc['합계'] = df.sum(axis=0)

        return df

    def get_index_size_df(self):
        index_size = self.get_index_size()

        df = {'total': index_size['total']}
        for k in index_size:
            if k == 'total':
                continue

            if k == 'etc':
                df[k] = pd.DataFrame({'count': index_size[k]}).fillna(0)
                df[k] = df[k].astype('float')
            else:
                df[k] = pd.DataFrame(index_size[k]).fillna(0)
                df[k] = df[k].astype('float')

                df[k].index.name = 'year'
                df[k].sort_index(inplace=True)

        return df

    def get_report(self, size_df):
        from IPython.display import display, HTML

        html = '<h1>전체 수량: {total:,.0f}</h1>'.format(total=size_df['total'])
        display(HTML(html))

        for k in size_df:
            if k == 'total':
                continue

            df = self.add_sum_column(size_df[k])

            html = '<style>.dataframe td { text-align: right; } .dataframe th { text-align: center; }</style>'
            html += '<h1>{title}: {total:,.0f}</h1>'.format(
                title=k,
                total=df.at['합계', '합계'],
            )
            html += df.to_html(index_names=False)
            display(HTML(html))

        return

    def get_report2(self, size_df):
        for k in size_df:
            if k == 'total':
                continue

            size_df[k].plot(kind='barh', figsize=(15, 10))

        return
