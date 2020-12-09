#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os import makedirs
from os.path import isdir
from time import sleep
from uuid import uuid1

import pytz
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.logger import Logger


class SeleniumProxyUtils(object):
    """프락시 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.args = None

        self.proxy = None
        self.proxy_server = None

        self.driver = None

        self.current_url = None

        self.url_buf = {}

        self.headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/79.0.3945.79 Safari/537.36'
        }

        self.timezone = pytz.timezone('Asia/Seoul')

        self.logger = Logger()

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
        import requests

        if self.driver is not None:
            return

        options = {
            'port': 8080
        }
        self.proxy_server = Server(self.args.proxy_server, options=options)

        self.proxy_server.start()

        _ = requests.post('http://{}:{}/proxy'.format(self.proxy_server.host, self.proxy_server.port))

        self.proxy = self.proxy_server.create_proxy()

        self.proxy.new_har(
            uuid1(),
            options={
                'captureHeaders': True,
                'captureContent': True,
                'captureBinaryContent': True
            }
        )

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

    def kill(self, proc_pid):
        import psutil

        try:
            process = psutil.Process(proc_pid)
            for proc in process.children(recursive=True):
                proc.kill()

            process.kill()
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '프로세서 킬 에러',
                'exception': str(e),
            })

        return

    def close_driver(self):
        self.kill(self.proxy_server.process.pid)

        try:
            self.proxy_server.stop()
            self.proxy.close()
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '프락시 종료 에러',
                'exception': str(e),
            })

        self.proxy_server = None

        self.proxy = None

        if self.driver is not None:
            self.driver.quit()
            self.driver = None

        return

    @staticmethod
    def make_path(data_path):
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
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'page down 에러',
                    'exception': str(e),
                })
                break

            sleep(2)

        return False

    def is_valid_path(self, path_list, url):
        if url in self.url_buf:
            return False

        for path in path_list:
            if url.find(path) < 0:
                continue

            return True

        return False

    def trace_networks(self, path_list):
        try:
            entry_list = self.proxy.har['log']['entries']
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'proxy entry 추출 에러',
                'exception': str(e),
            })

            return []

        result = []
        for ent in entry_list:
            url = ent['request']['url']
            if self.is_valid_path(path_list=path_list, url=url) is False:
                continue

            try:
                result.append({
                    'url': url,
                    'content': ent['response']['content']
                })
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'response content 추출 에러',
                    'exception': str(e),
                })

        return result

    def decode_response(self, content_list):
        import json
        import brotli
        from base64 import b64decode

        result = []
        for content in content_list:
            mime_type = content['content']['mimeType']
            if mime_type.find('json') < 0:
                continue

            try:
                text = content['content']['text']
                decoded_text = brotli.decompress(b64decode(text)).decode()

                doc = json.loads(decoded_text)
                if isinstance(doc, list):
                    for d in doc:
                        d['url'] = content['url']

                    result += doc
                else:
                    doc['url'] = content['url']
                    result.append(doc)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'decode response 에러',
                    'exception': str(e),
                })

        return result

    def check_history(self, url):
        if url in self.url_buf:
            return True

        self.url_buf[url] = 1

        return False

    def wait(self, css):
        wait = WebDriverWait(self.driver, 120)

        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css))
        )

        return

    @staticmethod
    def read_config(filename):
        """설정파일을 읽어드린다."""
        import json
        from glob import glob

        file_list = [filename]
        if isdir(filename) is True:
            file_list = []
            for f_name in glob('{}/*.json'.format(filename)):
                file_list.append(f_name)

        result = []

        for f_name in file_list:
            with open(f_name, 'r') as fp:
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
