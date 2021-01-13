#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pytz
import urllib3

from module.movie_reviews.cache_utils import CacheUtils
from utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class NaverMovieBase(object):

    def __init__(self, params):
        super().__init__()

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

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.params = params

        self.db = CacheUtils(
            filename=self.params.cache,
            use_cache=self.params.use_cache
        )
