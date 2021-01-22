#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from time import sleep
from urllib.parse import urlparse

import pytz
import urllib3
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver

from utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class SeleniumWireUtils(object):

    def __init__(self, login=False, headless=True, user_data_path=None, incognito=False,
                 executable_path='/usr/bin/chromedriver'):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.driver = None
        self.headers = None

        self.login = login
        self.headless = headless

        self.incognito = incognito

        self.user_data_path = user_data_path
        self.executable_path = executable_path

        self.open_driver()

    def open_driver(self):
        if self.driver is not None:
            return

        # from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        # capabilities = DesiredCapabilities.CHROME.copy()

        options = webdriver.ChromeOptions()

        options.add_argument('window-size=1920x1080')
        options.add_argument('disable-gpu')
        options.add_argument('disable-infobars')

        if self.incognito is True:
            options.add_argument("--incognito")

        options.add_argument('--no-sandbox')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--disable-extensions')
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors-spki-list')

        options.add_argument("--disable-xss-auditor")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-webgl")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--allow-running-insecure-content")

        options.add_argument("--no-default-browser-check")

        if self.headless is True:
            options.add_argument('headless')

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

    def scroll(self, meta, count=10, sleep_time=1, css_selector='html'):
        html = self.driver.find_element_by_css_selector(css_selector)

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

    def scroll_to(self, count, sleep_time=3):
        for _ in range(count):
            try:
                self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                self.driver.implicitly_wait(15)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'scroll error',
                    'exception': str(e),
                })
                break

            sleep(sleep_time)

        return False

    def open(self, url, resp_url_path=None, wait_for_path=None, clear_requests=True):
        if clear_requests is True:
            self.reset_requests()

        try:
            self.driver.get(url=url)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'url open error',
                'url': url,
                'error': str(e)
            })

        self.logger.log(msg={'level': 'MESSAGE', 'message': 'requests', 'url': url})

        if wait_for_path is None:
            self.driver.implicitly_wait(15)
            WebDriverWait(self.driver, 5, 10)

            return self.get_requests(resp_url_path=resp_url_path)

        try:
            self.driver.wait_for_request(wait_for_path, timeout=30)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'url open wait error',
                'url': url,
                'wait_for_path': wait_for_path,
                'error': str(e)
            })

        return self.get_requests(resp_url_path=resp_url_path)

    def get_requests(self, resp_url_path=None, max_try=10, sleep_time=10):
        if max_try < 0:
            return []

        try:
            req_list = self.driver.requests
        except Exception as e:
            self.logger.error(msg={
                'MESSAGE': 'get_requests 추출 에러',
                'error': str(e)
            })
            sleep(sleep_time)

            self.get_requests(resp_url_path=resp_url_path, max_try=max_try - 1)
            return []

        netloc = urlparse(self.driver.current_url).netloc
        token = netloc.split('.')
        if len(token) >= 3:
            netloc = '.'.join(token[1:])

        result = []
        for req in req_list:
            if req.response is None:
                continue

            if 'www.google' in req.url or 'googleapis' in req.url:
                continue

            if netloc not in req.url:
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

        if self.headers is None and len(req_list) > 0:
            self.headers = req_list[-1].headers

        return result

    def reset_requests(self):
        del self.driver.requests
        return
