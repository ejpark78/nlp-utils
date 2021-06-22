#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import math
import os
from datetime import datetime
from os.path import isdir, isfile
from urllib.parse import urlparse, parse_qs

import pytz
import requests
import urllib3
from tqdm import tqdm

from crawler.utils.logger import Logger
from crawler.utils.selenium_wire import SeleniumWireUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class UdemyBase(object):

    def __init__(self, params: dict):
        super().__init__()

        self.params = params

        self.logger = Logger()

        self.selenium = SeleniumWireUtils(
            login=self.params['login'],
            headless=self.params['headless'],
            user_data_path=self.params['user_data'],
        )

    @staticmethod
    def save_cache(cache: list, path: str, name: str, save_time_tag: bool = False) -> None:
        """캐쉬 파일로 저장한다."""
        if not isdir(path):
            os.makedirs(path)

        data_json = json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True)

        filename = f'{path}/{name}.json'
        with open(filename, 'w') as fp:
            fp.write(data_json)

        if save_time_tag is True:
            dt = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y%m%d-%H%M%S')
            with open(f'{path}/{name}.{dt}.json', 'w') as fp:
                fp.write(data_json)

        return

    @staticmethod
    def open_cache(path: str, name: str) -> list or None:
        """캐쉬파일을 읽는다."""
        filename = f'{path}/{name}.json'
        if isfile(filename) is False:
            return None

        with open(filename, 'r') as fp:
            data = ''.join(fp.readlines())
            result = json.loads(data)

        return result

    def download_file(self, url: str, filename: str) -> None:
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
                'error': f'error: {resp.text}'
            })

        total_size = int(resp.headers.get('content-length', 0))
        self.logger.log(msg={
            'size': f'size: {total_size:,}'
        })

        wrote, block_size = 0, 1024

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
    def parse_url(url: str) -> dict:
        """url 에서 쿼리문을 반환한다."""
        url_info = urlparse(url)
        query = parse_qs(url_info.query)
        for key in query:
            query[key] = query[key][0]

        return query

    def make_link_file(self, external_link: str, path: str, name: str) -> None:
        """외부 링크를 저장한다."""
        if 'external_url' not in external_link:
            return

        filename = f'{path}/{name}.desktop'
        if isfile(filename):
            self.logger.log(msg={
                'make_link_file': f'skip {filename}',
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
