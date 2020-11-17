#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from time import sleep

import pytz
import urllib3
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver

from module.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class SeleniumWireUtils(object):

    def __init__(self, login=False, headless=True, user_data_path=None, executable_path='/usr/bin/chromedriver'):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.driver = None
        self.login = login
        self.headless = headless
        self.user_data_path = user_data_path
        self.executable_path = executable_path

        self.headers = None

        self.open_driver()

    def open_driver(self):
        if self.driver is not None:
            return

        options = webdriver.ChromeOptions()

        if self.headless is True:
            options.add_argument('headless')

        options.add_argument('window-size=1920x1080')
        options.add_argument('disable-gpu')
        options.add_argument('disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-ssl-errors')

        if self.user_data_path is not None:
            options.add_argument('user-data-dir={}'.format(self.user_data_path))

        prefs = {
            'disk-cache-size': 4096,
            'profile.managed_default_content_settings.images': 2,
            'profile.default_content_setting_values.notifications': 2,
            'profile.managed_default_content_settings.stylesheets': 2,
            'profile.managed_default_content_settings.plugins': 1,
            'profile.managed_default_content_settings.popups': 2,
            'profile.managed_default_content_settings.geolocation': 2,
            'profile.managed_default_content_settings.media_stream': 2,
        }

        if self.login is True:
            prefs = {}

        options.add_experimental_option('prefs', prefs)

        self.driver = webdriver.Chrome(executable_path=self.executable_path, chrome_options=options)

        return

    def close_driver(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

        return

    def scroll(self, meta, count=10, sleep_time=1):
        """스크롤 한다."""
        html = self.driver.find_element_by_tag_name('html')

        for i in range(count):
            self.logger.log(msg={
                'level': 'INFO',
                'message': 'scroll',
                'scroll count': count - i,
                **meta
            })

            try:
                html.send_keys(Keys.PAGE_DOWN)

                self.driver.implicitly_wait(10)
                WebDriverWait(self.driver, 10, 10)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'page down error',
                    'exception': str(e),
                    **meta,
                })
                break

            sleep(sleep_time)

        return False

    def open(self, url, resp_url_path=None, wait_for_path=None, clear_requests=True):
        if clear_requests is True:
            del self.driver.requests

        self.driver.get(url=url)
        self.logger.log(msg={'level': 'MESSAGE', 'message': 'requests', 'url': url})

        if wait_for_path is not None:
            try:
                self.driver.wait_for_request(wait_for_path, timeout=30)
            except Exception as e:
                self.logger.error(msg={'wait_for_path': wait_for_path, 'error': str(e)})
        else:
            self.driver.implicitly_wait(15)
            WebDriverWait(self.driver, 5, 10)

        return self.get_requests(resp_url_path=resp_url_path)

    def get_requests(self, resp_url_path):
        result = []
        for req in self.driver.requests:
            if req.response is None:
                continue

            if resp_url_path is None:
                result.append(req)
                continue

            if resp_url_path not in req.url:
                continue

            if 'Content-Type' in req.response.headers and 'json' in req.response.headers['Content-Type']:
                try:
                    req.data = json.loads(req.response.body)
                except Exception as e:
                    self.logger.error(msg={'error': str(e)})

            self.headers = req.headers
            if 'Authorization' in req.headers:
                req.auth_token = req.headers['Authorization']

            result.append(req)

        return result
