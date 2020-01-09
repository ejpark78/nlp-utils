#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os import makedirs
from os.path import isdir

import pytz
from browsermobproxy import Server
from selenium import webdriver
from time import sleep
import uuid


class SeleniumProxyUtils(object):
    """유튜브 라이브 채팅 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.args = None

        self.proxy = None
        self.proxy_server = None

        self.driver = None

        self.url_buf = {}

        self.headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/79.0.3945.79 Safari/537.36'
        }

        self.timezone = pytz.timezone('Asia/Seoul')

    @staticmethod
    def parse_url(url):
        """url 에서 쿼리문을 반환한다."""
        from urllib.parse import urlparse, parse_qs

        url_info = urlparse(url)
        query = parse_qs(url_info.query)
        for key in query:
            query[key] = query[key][0]

        return query

    def open_driver(self):
        """브라우저를 실행한다."""
        if self.driver is not None:
            return

        self.proxy_server = Server('venv/bin/browsermob-proxy-2.1.4/bin/browsermob-proxy')

        self.proxy_server.start()

        self.proxy = self.proxy_server.create_proxy()
        self.proxy.new_har(uuid.uuid1())

        options = webdriver.ChromeOptions()

        options.add_experimental_option('w3c', False)

        if self.args.use_head is True:
            options.add_argument('headless')

        options.add_argument('--proxy-server={}'.format(self.proxy.proxy))
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--no-sandbox')
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('window-size=1200x600')
        options.add_argument('disable-infobars')

        if self.args.user_data is not None:
            options.add_argument('user-data-dir={}'.format(self.args.user_data))

        options.add_experimental_option('prefs', {
            'disk-cache-size': 4096,
            'profile.managed_default_content_settings.images': 2,
        })

        self.driver = webdriver.Chrome(chrome_options=options)

        return self.driver

    def close_driver(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

        self.proxy.close()
        self.proxy = None

        self.proxy_server.stop()
        self.proxy_server = None

        return

    @staticmethod
    def make_path(data_path):
        """ """
        if isdir(data_path) is True:
            return

        makedirs(data_path)
        return

    def page_down(self, count):
        """스크롤한다."""
        from selenium.webdriver.common.keys import Keys

        for _ in range(count):
            try:
                html = self.driver.find_element_by_tag_name('html')
                html.send_keys(Keys.PAGE_DOWN)
                self.driver.implicitly_wait(10)
            except Exception as e:
                print('page down error: ', e)
                break

            sleep(2)

        return False
