#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import splitext

import urllib3

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
        alias = {
            'score': 'rating',
            'code': 'movie_code',
            'comment': 'text',
            'author': 'username',
            'sympathy': 'like',
            'not_sympathy': 'dislike',
        }

        columns = list(set(
            'title,movie_code,username,date,rating,text,like,dislike'.split(',')
        ))

        db = CacheUtils(filename=self.params.cache)

        f_name = '{filename}.reviews'.format(filename=splitext(self.params.cache)[0])
        db.export_tbl(
            filename='{f_name}.json.bz2'.format(f_name=f_name),
            tbl='movie_reviews',
            db_column='no,title,date,code,review',
            json_columns='review'.split(','),
            date_columns='date'.split(','),
            columns=columns,
            alias=alias
        )
        db.json2xlsx(filename=f_name)

        f_name = '{filename}.movie_code'.format(filename=splitext(self.params.cache)[0])
        db.export_tbl(
            filename='{f_name}.json.bz2'.format(f_name=f_name),
            tbl='movie_code',
            db_column='title,code,date,review_count,total',
            json_columns=None,
            date_columns='date'.split(','),
            columns=None,
            alias={
                'code': 'movie_code'
            }
        )
        db.json2xlsx(filename=f_name)

        return

    def batch(self):
        if self.params.movie_code is True:
            NaverMovieCode(params=self.params).batch()

        if self.params.movie_reviews is True:
            NaverMovieReviews(params=self.params).batch()

        if self.params.upload is True:
            DataSetUtils().upload(filename=self.params.meta)

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

        parser.add_argument('--meta', default='./data/movie_reviews/naver-meta.json', help='메타 파일명')

        return parser.parse_args()


if __name__ == '__main__':
    NaverMovieReviewCrawler().batch()
