#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pytz
import urllib3

from module.movie_reviews.cache_utils import CacheUtils
from utils.logger import Logger
from utils.selenium_wire_utils import SeleniumWireUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DaumMovieBase(object):

    def __init__(self, params):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.params = params

        self.db = CacheUtils(
            filename=self.params.cache,
            use_cache=self.params.use_cache
        )

        self.selenium = SeleniumWireUtils()

        self.url = {
            'code': 'https://movie.daum.net/boxoffice/weekly?startDate={year}{month:02d}{day:02d}',
            'info': 'https://movie.daum.net/moviedb/main?movieId={code}',
            'grade': 'https://movie.daum.net/moviedb/grade?movieId={code}',
            'post': 'https://comment.daum.net/apis/v1/ui/single/main/@{code}',
            'reviews': 'https://comment.daum.net/apis/v1/posts/{post_id}/comments?'
                       'parentId=0&offset={offset}&limit=10&sort=RECOMMEND&isInitial=false&hasNext=true',
        }
