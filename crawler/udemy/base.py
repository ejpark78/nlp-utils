#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import math
import os
from datetime import datetime
from os.path import isfile
from urllib.parse import urlparse, parse_qs

import pytz
import requests
import urllib3
from tqdm import tqdm

from crawler.utils.logger import Logger
from crawler.utils.selenium_wire_utils import SeleniumWireUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class UdemyBase(object):

    def __init__(self, params):
        super().__init__()

        self.params = params

        self.logger = Logger()

        self.selenium = SeleniumWireUtils(
            login=self.params.login,
            headless=self.params.headless,
            user_data_path=self.params.user_data,
        )

    @staticmethod
    def save_cache(cache, path, name, save_time_tag=False):
        """캐쉬 파일로 저장한다."""
        data_json = json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True)

        filename = '{path}/{name}.json'.format(path=path, name=name)
        with open(filename, 'w') as fp:
            fp.write(data_json)

        if save_time_tag is True:
            dt = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y%m%d-%H%M%S')
            filename = '{path}/{name}.{dt}.json'.format(path=path, name=name, dt=dt)
            with open(filename, 'w') as fp:
                fp.write(data_json)

        return

    @staticmethod
    def open_cache(path, name):
        """캐쉬파일을 읽는다."""
        filename = '{path}/{name}.json'.format(path=path, name=name)
        if isfile(filename) is False:
            return None

        with open(filename, 'r') as fp:
            data = ''.join(fp.readlines())
            result = json.loads(data)

        return result

    def download_file(self, url, filename):
        self.logger.log({
            'level': 'MESSAGE',
            'message': '파일 다운로드',
            'url': url,
            'filename': filename,
        })

        resp = requests.get(
            url=url,
            allow_redirects=True,
            timeout=6000,
            verify=False,
            stream=True
        )

        if resp.status_code // 100 != 2:
            self.logger.error(msg={
                'error': 'error: {}'.format(resp.text)
            })

        total_size = int(resp.headers.get('content-length', 0))
        self.logger.log(msg={
            'size': 'size: {:,}'.format(total_size)
        })

        wrote = 0
        block_size = 1024

        with open(filename + '.parted', 'wb') as fp:
            pbar = tqdm(
                resp.iter_content(block_size),
                total=math.ceil(total_size // block_size), unit='KB',
                unit_scale=True
            )

            for data in pbar:
                wrote = wrote + len(data)
                fp.write(data)

        os.rename(filename + '.parted', filename)

        return

    @staticmethod
    def parse_url(url):
        """url 에서 쿼리문을 반환한다."""
        url_info = urlparse(url)
        query = parse_qs(url_info.query)
        for key in query:
            query[key] = query[key][0]

        return query

    def make_link_file(self, external_link, path, name):
        """외부 링크를 저장한다."""
        if 'external_url' not in external_link:
            return

        filename = '{path}/{name}.desktop'.format(path=path, name=name)
        if isfile(filename):
            self.logger.log(msg={
                'make_link_file': 'skip {}'.format(filename),
            })
            return

        with open(filename, 'w') as fp:
            content = '''
[Desktop Entry]
Encoding=UTF-8
Name={name}
Type=Link
URL={url}
Icon=text-html
'''.format(name=name, url=external_link['external_url'])

            fp.write(content)

        return
