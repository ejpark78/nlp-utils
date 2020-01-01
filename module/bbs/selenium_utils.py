#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
from time import sleep

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging.basicConfig(
    level=MESSAGE,
    format="[%(levelname)-s] %(message)s",
    handlers=[logging.StreamHandler()],
)


class SeleniumUtils(object):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.driver = None

    @staticmethod
    def open_driver(use_headless=True):
        """브라우저를 실행한다."""
        options = webdriver.ChromeOptions()

        if use_headless is True:
            options.add_argument('headless')

        options.add_argument('window-size=1920x1080')
        options.add_argument('disable-gpu')
        options.add_argument('disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-dev-shm-usage')

        options.add_argument('user-data-dir=selenium-data')

        options.add_experimental_option('prefs', {
            'disk-cache-size': 4096,
            'profile.managed_default_content_settings.images': 2,
        })

        return webdriver.Chrome(chrome_options=options)

    def scroll(self, count):
        """스크롤한다."""
        from selenium.webdriver.support.ui import WebDriverWait

        def check_height(prev_height):
            """현재 위치를 확인한다."""
            h = self.driver.execute_script("return document.body.scrollHeight")
            return h != prev_height

        scroll_time = 5
        last_height = -1

        for _ in range(count):
            try:
                height = self.driver.execute_script("return document.body.scrollHeight")

                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.driver.implicitly_wait(5)

                WebDriverWait(self.driver, scroll_time, 0.1).until(lambda x: check_height(height))
            except Exception as e:
                print('scroll error: ', e)
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

    @staticmethod
    def read_config(filename):
        """설정파일을 읽어드린다."""
        result = []

        with open(filename, 'r') as fp:
            buf = ''
            for line in fp.readlines():
                line = line.strip()
                if line.strip() == '' or line[0:2] == '//' or line[0] == '#':
                    continue

                buf += line
                if line != '}':
                    continue

                doc = json.loads(buf)
                buf = ''

                result.append(doc)

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

