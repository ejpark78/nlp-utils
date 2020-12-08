#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pytz

from module.facebook.cache_utils import CacheUtils
from module.facebook.parser import FBParser
from utils.elasticsearch_utils import ElasticSearchUtils
from utils.logger import Logger
from utils.selenium_utils import SeleniumUtils


class FBBase(object):

    def __init__(self, params):
        super().__init__()

        self.params = params

        self.timezone = pytz.timezone('Asia/Seoul')

        self.logger = Logger()

        self.parser = FBParser()

        self.selenium = SeleniumUtils(
            login=self.params.login,
            headless=self.params.headless,
            user_data_path=self.params.user_data,
        )

        self.db = None
        if self.params.cache is not None:
            self.db = CacheUtils(
                filename=self.params.cache,
                use_cache=self.params.use_cache
            )

        self.elastic = None
        if self.params.index is not None:
            self.elastic = ElasticSearchUtils(
                host=self.params.host,
                index=self.params.index,
                log_path=self.params.log_path,
                http_auth=self.params.auth,
                split_index=True,
            )
