#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from crawler.youtube.cache import Cache
from crawler.utils.logger import Logger
from crawler.utils.selenium_wire import SeleniumWireUtils


class YoutubeCore(object):

    def __init__(self, params: dict):
        super().__init__()

        self.params = params

        self.logger = Logger()

        self.db = Cache(filename=self.params['cache'])

        self.selenium = SeleniumWireUtils(
            login=self.params['login'],
            headless=self.params['headless'],
            user_data_path=self.params['user_data'],
        )
