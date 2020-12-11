#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os.path import splitext

import pytz
import urllib3
from dateutil.parser import parse as parse_date

from module.movie_reviews.cache_utils import CacheUtils
from module.movie_reviews.naver.movie_code import NaverMovieCode
from module.movie_reviews.naver.reviews import NaverMovieReviews
from utils.dataset_utils import DataSetUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class NaverMovieReviewCrawler(object):

    def __init__(self):
        super().__init__()

        self.params = self.init_arguments()

    def export(self):
        timezone = pytz.timezone('Asia/Seoul')

        db = CacheUtils(filename=self.params.cache)

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

        filename = '{}.reviews'.format(splitext(self.params.cache)[0])
        db.save(filename=filename, rows=data)

        return

    def batch(self):
        if self.params.movie_code is True:
            NaverMovieCode(params=self.params).batch()

        if self.params.movie_reviews is True:
            NaverMovieReviews(params=self.params).batch()

        if self.params.upload is True:
            DataSetUtils().upload(filename='data/movie_reviews/naver-meta.json')

        if self.params.export is True:
            self.export()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--movie-code', action='store_true', default=False, help='영화 코드 크롤링')
        parser.add_argument('--movie-reviews', action='store_true', default=False, help='리뷰 크롤링')

        parser.add_argument('--export', action='store_true', default=False, help='내보내기')
        parser.add_argument('--upload', action='store_true', default=False, help='minio 업로드')

        parser.add_argument('--cache', default='data/movie_reviews/naver.db', help='파일명')
        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--sleep', default=15, type=float, help='sleep time')

        return parser.parse_args()


if __name__ == '__main__':
    NaverMovieReviewCrawler().batch()
