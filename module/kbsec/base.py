#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
from os import makedirs, rename
from os.path import dirname, isdir, isfile

import requests
import urllib3
from tqdm import tqdm

from module.kbsec.cache_utils import CacheUtils
from utils.logger import Logger
from utils.selenium_wire_utils import SeleniumWireUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class KBSecBase(object):

    def __init__(self, params):
        super().__init__()

        # 070890 / 070890
        self.logger = Logger()

        self.params = params

        self.db = CacheUtils(
            filename=self.params.cache,
            use_cache=self.params.use_cache
        )

        self.selenium = SeleniumWireUtils(
            login=self.params.login,
            headless=self.params.headless,
            user_data_path=self.params.user_data,
        )

    def get_html(self, url, refresh=False, save_cache=True):
        content = None
        if refresh is False:
            content = self.db.fetch(url=url)

        is_cache = True
        if content is None:
            resp = requests.get(
                url=url,
                verify=False,
                timeout=120,
                headers=self.selenium.headers,
            )

            content = resp.content
            is_cache = False

        if is_cache is False and save_cache is True:
            self.db.save_cache(url=url, content=content)

        return content, is_cache

    def download_file(self, url, filename):
        if isfile(filename) is True:
            self.logger.log({
                'level': 'MESSAGE',
                'message': '파일이 이미 존재함',
                'url': url,
                'filename': filename,
            })
            return

        self.logger.log({
            'level': 'MESSAGE',
            'message': '파일 다운로드',
            'url': url,
            'filename': filename,
        })

        resp = requests.get(
            url=url,
            timeout=6000,
            verify=False,
            stream=True,
            headers=self.selenium.headers,
            allow_redirects=True,
        )

        if resp.status_code // 100 != 2:
            self.logger.error(msg={
                'error': 'error: {}'.format(resp.text)
            })

        total_size = int(resp.headers.get('content-length', 0))
        self.logger.log(msg={
            'size': 'size: {:,}'.format(total_size)
        })

        path = dirname(filename)
        if isdir(path) is False:
            makedirs(path)

        wrote = 0
        block_size = 1024

        with open(filename + '.parted', 'wb') as fp:
            p_bar = tqdm(
                resp.iter_content(block_size),
                total=math.ceil(total_size // block_size), unit='KB',
                unit_scale=True
            )

            for data in p_bar:
                wrote = wrote + len(data)
                fp.write(data)

        rename(filename + '.parted', filename)
        return
