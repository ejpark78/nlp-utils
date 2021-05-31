#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pytz

from crawler.facebook.cache_utils import CacheUtils
from crawler.facebook.parser import FacebookParser
from crawler.utils.es import ElasticSearchUtils
from crawler.utils.logger import Logger
from crawler.utils.selenium import SeleniumUtils


class FacebookCore(object):

    def __init__(self, params: dict):
        super().__init__()

        self.params = params

        self.timezone = pytz.timezone('Asia/Seoul')

        self.logger = Logger()

        self.parser = FacebookParser()

        self.selenium = SeleniumUtils(
            login=self.params['login'],
            headless=self.params['headless'],
            user_data_path=self.params['user_data'],
        )

        self.db = None
        if self.params['cache'] is not None:
            self.db = CacheUtils(
                filename=self.params['cache'],
                use_cache=self.params['use_cache']
            )

        self.elastic = None
        if self.params['index'] is not None:
            self.elastic = ElasticSearchUtils(
                host=self.params['host'],
                index=self.params['index'],
                log_path=self.params['log_path'],
                http_auth=self.params['auth'],
            )
