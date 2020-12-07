#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.logger import Logger


class SeleniumUtils(object):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self, login=False, headless=True, user_data_path=None, incognito=False,
                 executable_path='/usr/bin/chromedriver'):
        """ 생성자 """
        super().__init__()

        self.driver = None

        self.login = login
        self.headless = headless
        self.incognito = incognito
        self.user_data_path = user_data_path
        self.executable_path = executable_path

        self.logger = Logger()

        self.open_driver()

    def open_driver(self):
        """브라우저를 실행한다."""
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

    def open(self, url, wait_for_path=None):
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
            return

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

        return

    def page_down(self, count, sleep_time=2):
        """스크롤한다."""
        html = self.driver.find_element_by_tag_name('html')

        for _ in range(count):
            try:
                html.send_keys(Keys.PAGE_DOWN)
                self.driver.implicitly_wait(10)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'page down error',
                    'exception': str(e),
                })
                break

            sleep(sleep_time)

        return False

    def scroll(self, count):
        """스크롤한다."""

        def check_height(prev_height):
            """현재 위치를 확인한다."""
            h = self.driver.execute_script('return document.body.scrollHeight')
            return h != prev_height

        scroll_time = 5
        last_height = -1

        for _ in range(count):
            try:
                height = self.driver.execute_script('return document.body.scrollHeight')

                self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                self.driver.implicitly_wait(15)

                WebDriverWait(self.driver, scroll_time, 10).until(lambda x: check_height(height))
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'scroll error',
                    'exception': str(e),
                })
                break

            if last_height == height:
                return True

            last_height = height
            sleep(5)

        return False

    def wait(self, css):
        wait = WebDriverWait(self.driver, 120)

        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css))
        )

        return

    def wait_clickable(self, css):
        wait = WebDriverWait(self.driver, 120)

        wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css))
        )

        return

    @staticmethod
    def replace_tag(html_tag, tag_list, replacement='', attribute=None):
        """ html 태그 중 특정 태그를 삭제한다. ex) script, caption, style, ... """
        if html_tag is None:
            return False

        for tag_name in tag_list:
            for tag in html_tag.find_all(tag_name, attrs=attribute):
                if replacement == '':
                    tag.extract()
                else:
                    tag.replace_with(replacement)

        return True

    @staticmethod
    def parse_url(url):
        """url 에서 쿼리문을 반환한다."""
        url_info = urlparse(url)
        query = parse_qs(url_info.query)
        for key in query:
            query[key] = query[key][0]

        return query
