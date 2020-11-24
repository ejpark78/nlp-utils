#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from os.path import splitext
from time import sleep
from urllib.parse import urljoin

import pandas as pd
import pytz
import urllib3
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from module.movie_reviews.cache_utils import CacheUtils
from utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class NaverMovieReviews(object):

    def __init__(self):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.params = self.init_arguments()

        self.sleep_time = 15

        self.url = {
            'code': 'https://movie.naver.com/movie/sdb/browsing/bmovie.nhn?open={year}&page={page}',
            'info_basic': 'https://movie.naver.com/movie/bi/mi/basic.nhn?code={code}',
            'info_detail': 'https://movie.naver.com/movie/bi/mi/detail.nhn?code={code}',
            'info_point': 'https://movie.naver.com/movie/bi/mi/point.nhn?code={code}',
            'info_review': 'https://movie.naver.com/movie/bi/mi/review.nhn?code={code}',
            'reviews': 'https://movie.naver.com/movie/bi/mi/pointWriteFormList.nhn?'
                       'code={code}&type=after&isActualPointWriteExecute=false&isMileageSubscriptionAlready=false&'
                       'isMileageSubscriptionReject=false&page={page}',
        }

        self.db = CacheUtils(filename=self.params.filename)
        self.db.use_cache = self.params.use_cache

    def __del__(self):
        pass

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

    def get_movie_code(self):
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
                    sleep(self.sleep_time)

        return

    def save_movie_reviews(self, code, title, content, meta):
        soup = BeautifulSoup(content, 'html5lib')

        buf = set()
        count = 0
        for item in soup.select('div.score_result ul li'):
            p = item.select('div.score_reple p')[0]
            span = p.select('span')

            comment = span[-1].get_text('\n').strip() if span is not None and len(span) > 0 else ''

            if comment == '':
                comment = p.get_text('\n').strip()

            review = {
                'code': code,
                'title': title,
                'score': ','.join([x.get_text() for x in item.select('div.star_score em')]),
                'comment': comment,
                'is_viewer': ','.join([x.get_text() for x in p.select('span.ico_viewer')]),
                'author': item.select('div.score_reple dl dt em span')[0].get_text(),
                'date': item.select('div.score_reple dl dt em')[-1].get_text(),
                'sympathy': item.select('div.btn_area a._sympathyButton strong')[-1].get_text(),
                'not_sympathy': item.select('div.btn_area a._notSympathyButton strong')[-1].get_text(),
            }

            if review['comment'] == '':
                continue

            buf.add(review['comment'])
            buf.add(review['date'])

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '영화 리뷰 저장',
                'count': len(buf) / 2 if len(buf) > 0 else 0,
                'date': review['date'],
                'score': review['score'],
                'comment': review['comment'],
                **meta
            })

            try:
                self.db.cursor.execute(
                    self.db.template['reviews'],
                    (title, code, json.dumps(review, ensure_ascii=False),)
                )

                count += 1
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '영화 리뷰 저장 오류',
                    'error': str(e),
                    **meta
                })

        self.db.conn.commit()

        return {
            'list': ','.join(list(buf)),
            'count': count
        }

    def get_movie_reviews(self):
        _ = self.db.cursor.execute('SELECT code, title FROM movie_code WHERE review_count < 0')

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            (code, title) = (item[0], item[1])

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '영화 정보',
                'code': code,
                'title': title,
                'position': '{:,}/{:,}'.format(i, len(rows)),
            })

            prev = ''
            count = 0
            for p in range(1, 1000):
                url = self.url['reviews'].format(code=code, page=p)

                contents = self.db.read_cache(
                    url=url,
                    meta={
                        'title': title,
                        'page': p,
                        'position': '{:,}/{:,}'.format(i, len(rows)),
                    }
                )
                review_info = self.save_movie_reviews(
                    title=title,
                    code=code,
                    content=contents['content'],
                    meta={
                        'title': title,
                        'url': url,
                        'page': p,
                        'position': '{:,}/{:,}'.format(i, len(rows)),
                    }
                )
                count += review_info['count']

                if review_info['list'] == '':
                    self.logger.log(msg={
                        'level': 'MESSAGE',
                        'message': '영화 리뷰 없음',
                    })
                    break
                elif prev == review_info['list']:
                    self.logger.log(msg={
                        'level': 'MESSAGE',
                        'message': '영화 리뷰 중복',
                        'review_list': review_info['list'].split(',')
                    })
                    break

                prev = review_info['list']

                if contents['is_cache'] is False:
                    sleep(self.sleep_time)

            self.db.update_review_count(code=code, count=count)

        return

    def export(self):
        timezone = pytz.timezone('Asia/Seoul')

        db = CacheUtils(filename=self.params.filename)

        column = 'no,title,code,review'
        db.cursor.execute('SELECT {} FROM movie_reviews'.format(column))

        rows = db.cursor.fetchall()

        data = []
        for i, item in enumerate(rows):
            r = dict(zip(column.split(','), item))

            review = json.loads(r['review'])
            del r['review']

            review['date'] = parse_date(review['date']).astimezone(timezone).isoformat()

            r.update(review)

            data.append(r)

        df = pd.DataFrame(data)

        filename = '{}.reviews'.format(splitext(self.params.filename)[0])

        # json
        df.to_json(
            filename + '.json.bz2',
            force_ascii=False,
            compression='bz2',
            orient='records',
            lines=True,
        )

        # xlsx
        self.save_excel(filename=filename, df=df)

        return

    @staticmethod
    def save_excel(filename, df, size=500000):
        writer = pd.ExcelWriter(filename + '.xlsx', engine='xlsxwriter')

        if len(df) > size:
            for pos in range(0, len(df), size):
                end_pos = pos + size if len(df) > (pos + size) else len(df)

                df[pos:pos + size].to_excel(
                    writer,
                    index=False,
                    sheet_name='{:,}-{:,}'.format(pos, end_pos)
                )
        else:
            df.to_excel(writer, index=False, sheet_name='review')

        writer.save()
        return

    def batch(self):
        if self.params.movie_code is True:
            self.get_movie_code()

        if self.params.movie_reviews is True:
            self.get_movie_reviews()

        if self.params.export is True:
            self.export()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--movie-code', action='store_true', default=False, help='영화 코드 크롤링')
        parser.add_argument('--movie-reviews', action='store_true', default=False, help='리뷰 크롤링')

        parser.add_argument('--export', action='store_true', default=False, help='내보내기')

        parser.add_argument('--filename', default='data/movie_reviews/naver.db', help='파일명')

        return parser.parse_args()


if __name__ == '__main__':
    NaverMovieReviews().batch()
