#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

import pytz
import urllib3
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver

from module.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class SeleniumWireUtils(object):

    def __init__(self):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.driver = None
        self.login = False
        self.headless = True
        self.user_data_path = None
        self.executable_path = '/usr/bin/chromedriver'

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

    def open(self, url, wait_for_path):
        del self.driver.requests

        self.driver.get(url=url)

        if wait_for_path is not None:
            self.driver.wait_for_request(wait_for_path, timeout=30)
        else:
            self.driver.implicitly_wait(15)
            WebDriverWait(self.driver, 5, 10)

        result = []
        for req in self.driver.requests:
            if req.response is None:
                continue

            if '/apis/' not in req.url:
                continue

            req.data = json.loads(req.response.body)
            req.auth_token = req.headers['Authorization']

            self.headers = req.headers

            result.append(req)

        return result
