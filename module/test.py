#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin

import urllib3
from dateutil.parser import parse as date_parse
from dateutil.rrule import rrule, DAILY
from time import sleep

from module.crawler_base import CrawlerBase
from module.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=MESSAGE)


class SeleniumCrawler(object):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self, job_category='', job_id='', column=''):
        """ 생성자 """
        super().__init__()

        self.job_category = job_category
        self.job_id = job_id
        self.column = column

    def batch(self):
        """"""
        import os
        from time import sleep
        from selenium import webdriver
        from bs4 import BeautifulSoup

        url = 'https://m.cafe.naver.com/xst'

        options = webdriver.ChromeOptions()

        # options.add_argument('headless')
        # options.add_argument('window-size=800x600')

        options.add_argument('disable-infobars')
        options.add_argument('--dns-prefetch-disable')

        options.add_argument('user-data-dir=selenium-data')
        # options.add_argument('--no-sandbox')

        path = os.path.dirname(os.path.realpath(__file__))

        driver = webdriver.Chrome('{pwd}/chromedriver'.format(pwd=path), chrome_options=options)
        driver.implicitly_wait(3)

        driver.get(url)
        driver.implicitly_wait(60)

        # '//*[@id="btnNextList"]/a'

        return


if __name__ == '__main__':
    util = SeleniumCrawler()

    util.batch()
