#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import os
from os import makedirs
from os.path import dirname, isdir
from time import sleep
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging.basicConfig(
    format="[%(levelname)-s] %(message)s",
    handlers=[logging.StreamHandler()],
    level=MESSAGE,
)


class SeleniumCrawler(object):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        path = os.path.dirname(os.path.realpath(__file__))
        self.driver_path = '{pwd}/chromedriver'.format(pwd=path)

        self.driver = None

        self.use_see_more_link = True

    def open_driver(self):
        """브라우저를 실행한다."""
        options = webdriver.ChromeOptions()

        options.add_argument('--dns-prefetch-disable')
        options.add_argument('disable-infobars')
        options.add_argument('user-data-dir=selenium-data')

        options.add_experimental_option('prefs', {
            'disk-cache-size': 4096,
            'profile.managed_default_content_settings.images': 2,
        })

        return webdriver.Chrome(self.driver_path, chrome_options=options)

    def fb_login(self, user, password):
        """로그인한다."""
        if self.driver is None:
            self.driver = self.open_driver()

        self.driver.get('https://www.facebook.com/')
        self.driver.implicitly_wait(3)

        assert 'Facebook' in self.driver.title

        elem = self.driver.find_element_by_id("email")
        elem.send_keys(user)
        self.driver.implicitly_wait(4)

        elem = self.driver.find_element_by_id("pass")
        elem.send_keys(password)
        self.driver.implicitly_wait(3)

        elem.send_keys(Keys.RETURN)
        self.driver.implicitly_wait(5)

        return

    def scroll(self, count):
        """스크롤한다."""

        def check_height(prev_height):
            """현재 위치를 확인한다."""
            h = self.driver.execute_script("return document.body.scrollHeight")
            return h != prev_height

        scroll_time = 5
        last_height = -1

        for _ in tqdm(range(count), desc='scroll', dynamic_ncols=True):
            try:
                height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.driver.implicitly_wait(5)

                self.see_more_link()

                WebDriverWait(self.driver, scroll_time, 0.1).until(lambda x: check_height(height))
            except Exception as e:
                print('scroll error: ', e)
                break

            if last_height == height:
                return True

            last_height = height
            sleep(5)

        return False

    def parse_contents(self, url, html):
        """포스트 내용을 추출한다."""
        soup = BeautifulSoup(html, 'html5lib')

        # css_list = [
        #     {
        #         'type': '그룹',
        #         'attr': {'class': '_5pcr userContentWrapper'}
        #     }
        # ]
        #
        # tag_list = []
        # for css in css_list:
        #     tag_list += soup.find_all('div', css['attr'])

        tag_list = soup.find_all('article')

        result = []
        for box in tag_list:
            post = dict()

            post['html'] = str(box)

            # data-store
            if box.has_attr('data-store'):
                post['data-store'] = json.loads(box['data-store'])

            # data-fit
            if box.has_attr('data-fit'):
                post['data-fit'] = json.loads(box['data-fit'])

            # 메세지 추출
            post['message'] = [str(v) for v in box.find_all('span', {'data-sigil': 'expose'})]

            # 공감 정보
            post['reactions'] = [str(v) for v in box.find_all('div', {'data-sigil': 'reactions-sentence-container'})]

            result.append(post)

        # 태그 삭제
        self.delete_post()

        return result

    def delete_post(self):
        """태그 삭제"""
        script = 'document.querySelectorAll("article").forEach(function(ele) {ele.remove();})'

        try:
            self.driver.execute_script(script)
        except Exception as e:
            print(e)
            return None

        self.driver.implicitly_wait(10)

        return

    @staticmethod
    def save_posts(post_list, page, count):
        """추출한 정보를 저장한다."""
        filename = '../data/facebook/{name}/{count:05d}.json'.format(name=page['name'], count=count)

        path = dirname(filename)
        if isdir(path) is False:
            makedirs(path)

        with open(filename, 'w') as fp:
            for post in post_list:
                line = json.dumps(post, ensure_ascii=False, indent=4) + '\n'
                fp.write(line)

        return

    def see_more_link(self):
        """ 더 보기 링크를019! 클릭한다."""
        if self.use_see_more_link is False:
            return

        try:
            self.driver.find_element_by_link_text('더 보기').click()
        except Exception as e:
            print('more link error: ', e)

        return

    def get_page(self, page):
        """하나의 계정을 모두 읽어드린다."""
        if self.driver is None:
            self.driver = self.open_driver()

        url = '{site}/{page}'.format(**page)

        self.use_see_more_link = False

        self.driver.get(url)
        self.driver.implicitly_wait(10)

        for i in tqdm(range(50000)):
            stop = self.scroll(5)
            self.driver.implicitly_wait(5)

            try:
                post_list = self.parse_contents(
                    url=url,
                    html=self.driver.page_source,
                )
            except Exception as e:
                print('get page error: ', e)
                continue

            if post_list is None or len(post_list) == 0:
                break

            self.save_posts(post_list=post_list, page=page, count=i)

            if stop is True:
                break

        self.driver.quit()
        self.driver = None

        return

    def batch(self):
        """ """
        with open('../page.list', 'r') as fp:
            page_list = [json.loads(l) for l in fp.readlines() if l.strip() != '' and l[0] != '#']

        for p in page_list:
            self.get_page(page=p)

        return


if __name__ == '__main__':
    # https://stackabuse.com/getting-started-with-selenium-and-python/

    utils = SeleniumCrawler()

    # utils.fb_login(user='ejpark78@gmail.com', password='ajswl@2019@')

    utils.batch()
