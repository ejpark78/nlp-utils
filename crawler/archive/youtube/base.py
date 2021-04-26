#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from crawler.youtube.cache_utils import CacheUtils
from crawler.utils.logger import Logger
from crawler.utils.selenium_wire import SeleniumWireUtils


class YoutubeBase(object):

    def __init__(self, params):
        super().__init__()

        self.params = params

        self.logger = Logger()

        self.db = CacheUtils(
            filename=self.params.cache,
            use_cache=self.params.use_cache
        )

        self.selenium = SeleniumWireUtils(
            login=self.params.login,
            headless=self.params.headless,
            user_data_path=self.params.user_data,
        )
