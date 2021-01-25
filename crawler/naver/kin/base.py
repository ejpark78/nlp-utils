#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from datetime import datetime
from os import getenv
from time import sleep

import pytz
import requests
import urllib3
import yaml
from cachelib import SimpleCache

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.utils.html_parser import HtmlParser
from crawler.utils.logger import Logger
from crawler.web_news.post_process import PostProcessUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class NaverKinBase(object):
    """크롤러 베이스"""

    def __init__(self):
        super().__init__()

        self.debug = int(getenv('DEBUG', 0))

        self.config = None

        self.headers = {
            'mobile': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                              'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                              'Version/11.0 Mobile/15A372 Safari/604.1'
            },
            'desktop': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/87.0.4280.141 Safari/537.36'
            }
        }

        self.sleep_time = 2

        # 로컬 시간 정보
        self.timezone = pytz.timezone('Asia/Seoul')

        self.logger = Logger()

    @staticmethod
    def open_config(filename: str) -> dict:
        with open(filename, 'r') as fp:
            return dict(yaml.load(stream=fp, Loader=yaml.FullLoader))
