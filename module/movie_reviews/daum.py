#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os.path import splitext

import urllib3

from module.movie_reviews.cache_utils import CacheUtils
from module.movie_reviews.daum.movie_code import DaumMovieCode
from module.movie_reviews.daum.reviews import DaumMovieReviews

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DaumMovieReviewCrawler(object):

    def __init__(self):
        super().__init__()

        self.params = self.init_arguments()

    def export(self):
        db = CacheUtils(filename=self.params.cache)

        column = 'no,title,code,review'
        db.cursor.execute('SELECT {} FROM movie_reviews'.format(column))

        rows = db.cursor.fetchall()

        keys = 'id,postId,rating,content,childCount,likeCount,dislikeCount,recommendCount'.split(',')

        data = []
        for i, item in enumerate(rows):
            r = dict(zip(column.split(','), item))

            review = json.loads(r['review'])
            del r['review']

            r['username'] = review['userId']
            if 'displayName' in review['user']:
                r['username'] = review['user']['displayName']

            r['date'] = review['createdAt']

            for k in keys:
                if k not in review:
                    continue

                r[k] = review[k]
                if isinstance(review[k], str):
                    r[k] = str(review[k]).strip()

            data.append(r)

        filename = '{}.reviews'.format(splitext(self.params.cache)[0])
        db.save(filename=filename, rows=data)

        return

    def batch(self):
        if self.params.movie_code is True:
            DaumMovieCode(params=self.params).batch()

        if self.params.movie_reviews is True:
            DaumMovieReviews(params=self.params).batch()

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

        parser.add_argument('--cache', default='data/movie_reviews/daum.db', help='파일명')
        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--sleep', default=15, type=float, help='sleep time')

        return parser.parse_args()


if __name__ == '__main__':
    DaumMovieReviewCrawler().batch()
