#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from module.web_news import WebNewsCrawler

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class YonhapNewsCrawler(WebNewsCrawler):
    """연합뉴스 크롤링"""

    def __init__(self):
        """ 생성자 """
        super().__init__(job_id='yonhapnews', column='trace_list')
