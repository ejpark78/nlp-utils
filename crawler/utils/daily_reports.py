#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import pytz
import urllib3
from IPython.display import display
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from matplotlib import font_manager, rc

from crawler.utils.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DailyReports(object):

    def __init__(self, host: str = 'https://corpus.ncsoft.com:9200', auth: str = 'ZWxhc3RpYzpubHBsYWI=',
                 encoded_auth: bool = True):
        super().__init__()

        plt.style.use('ggplot')

        plt.rcParams.update({'font.size': 15})
        plt.figure(figsize=(20, 20))

        pd.set_option('precision', 0)
        pd.options.display.float_format = '{:,.0f}'.format

        self.today = datetime.now(tz=pytz.timezone('Asia/Seoul'))
        self.yesterday = self.today - relativedelta(days=1)

        self.es = ElasticSearchUtils(host=host, http_auth=auth, encoded_auth=encoded_auth)

        self.state = {
            'list': self.es.get_index_list(),
            'size': self.es.get_index_size()
        }

    @staticmethod
    def custom_display(df: pd.DataFrame) -> None:
        pd.set_option('display.float_format', '{:.1f}'.format)
        display(df.style.set_properties(**{
            'text-align': 'right',
            'background-color': 'white',
            'border-color': 'white',
            'color': 'black'
        }))
        return

    @staticmethod
    def set_plt_font() -> None:
        """matplotlib 한글 폰트 설정"""
        font_path = '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf'
        rc('font', family=font_manager.FontProperties(fname=font_path).get_name())
        return

    @staticmethod
    def merge_category(category_count: list) -> dict:
        cnt = defaultdict(int)

        for item in category_count:
            for c in item['category'].split(','):
                cnt[c] += item['count']

        return cnt

    @staticmethod
    def get_date_range_dsl(date_range: str = None, date_column: str = 'date') -> dict:
        if date_range is None:
            return {}

        dt_start, dt_end = None, None
        if date_range is not None:
            dt_start, dt_end = date_range.split('~')
            dt_start, dt_end = parse_date(dt_start), parse_date(dt_end)

        fmt, search_fmt = 'yyyy-MM-dd HH:mm:ss', '%Y-%m-%d %H:%M:%S'

        if dt_start == dt_end:
            dt_end += relativedelta(days=1) - relativedelta(seconds=1)

        return {
            'query': {
                'bool': {
                    'must': {
                        'range': {
                            date_column: {
                                'gte': dt_start.strftime(search_fmt),
                                'lte': dt_end.strftime(search_fmt),
                                'format': fmt
                            }
                        }
                    }
                }
            }
        }

    def get_date_histogram(self, index: str, column: str = 'date', interval: str = 'day',
                           date_format: str = 'yyyy-MM-dd', date_range: str = None) -> dict:
        """ 날짜별 문서 수량을 조회한다. """
        query = {
            'size': 0,
            'track_total_hits': True,
            'aggregations': {
                'by_date': {
                    'date_histogram': {
                        'field': column,
                        'keyed': False,
                        'format': date_format,
                        'time_zone': '+09:00',
                        'calendar_interval': interval
                    }
                }
            }
        }

        query.update(self.get_date_range_dsl(date_range=date_range, date_column=column))

        resp = self.es.conn.search(index=index, body=query)

        buckets = resp['aggregations']['by_date']['buckets']
        rows = [{'date': x['key_as_string'], 'count': x['doc_count']} for x in buckets]

        return {
            'total': resp['hits']['total']['value'],
            'rows': rows,
        }

    def get_column_count(self, index: str, column: str = 'date', date_column: str = 'date',
                         date_range: str = None) -> list:
        """ 필드의 문서 수량을 조회한다. """
        query = {
            'size': 0,
            'aggregations': {
                'group_by': {
                    'terms': {
                        'field': f'{column}',
                        'size': 200
                    }
                }
            }
        }

        query.update(self.get_date_range_dsl(date_range=date_range, date_column=date_column))

        resp = self.es.conn.search(index=index, body=query)

        count = resp['aggregations']['group_by']['buckets']

        total = 0
        for x in count:
            total += x['doc_count']

        result = []
        for x in count:
            result.append({
                column: x['key'],
                'count': x['doc_count']
            })

        return sorted(result, key=lambda item: item[column])

    def get_index_histogram(self, index_list: str, column: str = 'date', interval: str = 'day',
                            date_format: str = 'yyyy-MM-dd', date_range: str = None) -> dict:
        """ 날짜별 문서 수량을 조회한다. """
        query = {
            'size': 0,
            'track_total_hits': True,
            'aggregations': {
                'by_index': {
                    'terms': {
                        'field': '_index',
                        'size': 100
                    },
                    'aggregations': {
                        'by_date': {
                            'date_histogram': {
                                'field': column,
                                'keyed': False,
                                'format': date_format,
                                'time_zone': '+09:00',
                                'calendar_interval': interval
                            }
                        }
                    }
                }
            }
        }

        query.update(self.get_date_range_dsl(date_range=date_range, date_column=column))

        resp = self.es.conn.search(index=index_list, body=query)

        result = defaultdict(dict)

        buckets = resp['aggregations']['by_index']['buckets']
        for item in buckets:
            sec_name = item['key'].split('-')[2]

            for x in item['by_date']['buckets']:
                result[sec_name][x['key_as_string']] = x['doc_count']

        return result


if __name__ == '__main__':
    reports = DailyReports()

    reports.set_plt_font()
