#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import splitext

import urllib3

from module.movie_reviews.cache_utils import CacheUtils
from module.movie_reviews.daum.movie_code import DaumMovieCode
from module.movie_reviews.daum.reviews import DaumMovieReviews
from utils.dataset_utils import DataSetUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DaumMovieReviewCrawler(object):

    def __init__(self):
        super().__init__()

        self.params = self.init_arguments()

    def export(self):
        alias = {
            'code': 'movie_code',
            'content': 'text',
            'postId': 'post_id',
            'id': 'reply_id',
            'userId': 'username',
            'user.displayName': 'username',
            'createdAt': 'date',
            'likeCount': 'like',
            'dislikeCount': 'dislike',
            'recommendCount': 'recommend',
            'childCount': 'reply',
        }

        columns = list(set(
            'title,movie_code,username,date,post_id,rating,text,'
            'reply,like,dislike,recommend'.split(',')
        ))

        db = CacheUtils(filename=self.params.cache)

        db.export_tbl(
            filename='{filename}.{tbl}.json.bz2'.format(
                tbl='reviews',
                filename=splitext(self.params.cache)[0]
            ),
            tbl='movie_reviews',
            db_column='no,title,date,code,review',
            json_columns='review'.split(','),
            date_columns='date'.split(','),
            columns=columns,
            alias=alias
        )

        db.export_tbl(
            filename='{filename}.{tbl}.json.bz2'.format(
                tbl='movie_code',
                filename=splitext(self.params.cache)[0]
            ),
            tbl='movie_code',
            db_column='title,code,date,review_count,total',
            json_columns=None,
            date_columns='date'.split(','),
            columns=None,
            alias={
                'code': 'movie_code'
            }
        )

        return

    def batch(self):
        if self.params.movie_code is True:
            DaumMovieCode(params=self.params).batch()

        if self.params.movie_reviews is True:
            DaumMovieReviews(params=self.params).batch()

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
        parser.add_argument('--movie-info', action='store_true', default=False, help='영화 정보 크롤링')
        parser.add_argument('--movie-reviews', action='store_true', default=False, help='리뷰 크롤링')

        parser.add_argument('--export', action='store_true', default=False, help='내보내기')
        parser.add_argument('--upload', action='store_true', default=False, help='minio 업로드')

        parser.add_argument('--cache', default='data/movie_reviews/daum.db', help='파일명')
        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--sleep', default=15, type=float, help='sleep time')

        parser.add_argument('--meta', default='./data/movie_reviews/daum-meta.json', help='메타 파일명')

        return parser.parse_args()


if __name__ == '__main__':
    DaumMovieReviewCrawler().batch()
