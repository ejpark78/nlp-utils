#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from glob import glob
from os.path import isdir
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from module.utils.logger import Logger


class SeleniumUtils(object):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.env = None
        self.driver = None

        self.logger = Logger()

    def open_driver(self):
        """브라우저를 실행한다."""
        if self.driver is not None:
            return

        options = webdriver.ChromeOptions()

        if self.env.use_head is True:
            options.add_argument('headless')

        options.add_argument('window-size=1920x1080')
        options.add_argument('disable-gpu')
        options.add_argument('disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-dev-shm-usage')

        if self.env.user_data is not None:
            options.add_argument('user-data-dir={}'.format(self.env.user_data))

        options.add_experimental_option('prefs', {
            'disk-cache-size': 4096,
            'profile.managed_default_content_settings.images': 2,
        })

        chrome_driver = self.env.driver
        self.driver = webdriver.Chrome(executable_path=chrome_driver, chrome_options=options)

        return

    def close_driver(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

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
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'page down error',
                    'exception': str(e),
                })
                break

            sleep(2)

        return False

    def scroll(self, count):
        """스크롤한다."""
        from selenium.webdriver.support.ui import WebDriverWait

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
        """ """
        wait = WebDriverWait(self.driver, 120)

        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css))
        )

        return

    def wait_clickable(self, css):
        """ """
        wait = WebDriverWait(self.driver, 120)

        wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css))
        )

        return

    @staticmethod
    def read_config(filename):
        """설정파일을 읽어드린다."""
        file_list = [filename]
        if isdir(filename) is True:
            file_list = []
            for f_name in glob('{}/*.json'.format(filename)):
                file_list.append(f_name)

        result = []
        for f_name in file_list:
            with open(f_name, 'r') as fp:
                doc = json.load(fp)
                result += doc['list']

        return result

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
        from urllib.parse import urlparse, parse_qs

        url_info = urlparse(url)
        query = parse_qs(url_info.query)
        for key in query:
            query[key] = query[key][0]

        return query
