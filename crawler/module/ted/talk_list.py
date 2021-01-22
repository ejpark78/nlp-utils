#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from glob import glob
from time import sleep
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from module.ted.base import TedBase


class TedTalkList(TedBase):

    def __init__(self, params):
        super().__init__(params=params)

    def get_max_page(self, url):
        resp = self.get_html(url=url)
        if resp is None:
            sleep(self.params.sleep)
            return -1

        soup = BeautifulSoup(resp.content, 'lxml')

        page_list = soup.select('div.pagination a')

        return max([int(x.get_text()) for x in page_list if x.get_text().isdecimal()])

    def parse_talk_list(self, url):
        resp = self.get_html(url=url)
        if resp is None:
            sleep(self.params.sleep)
            return

        soup = BeautifulSoup(resp.content, 'lxml')

        result = [urljoin(url, x['href']) for x in soup.select('div.col a.ga-link') if x.has_attr('href')]

        return list(set(result))

    def batch(self):
        max_page = self.get_max_page(url='https://www.ted.com/talks')

        with open(self.filename['url_list'], 'r') as fp:
            url_list = json.load(fp=fp)

        for page in range(max_page, 0, -1):
            url = self.page_url.format(page=page)

            url_list += self.parse_talk_list(url=url)

            self.logger.log({
                'method': 'trace_list',
                'page': page,
                'url': url,
                'talk_list': len(url_list),
            })
            sleep(self.params.sleep)

            with open(self.filename['url_list'], 'w') as fp:
                url_list = list(set(url_list))
                fp.write(json.dumps(url_list, ensure_ascii=False, indent=4))

        return

    def update_talk_list(self):
        talk_list = {}
        for f in glob('data/ted/*/talk-info.json'):
            self.logger.log({'filename': f})

            with open(f, 'r') as fp:
                info = json.load(fp=fp)

            talk_list[info['url']] = info['talk_id']

        with open(self.filename['talk_list'], 'w') as fp:
            fp.write(json.dumps(talk_list, ensure_ascii=False, indent=4))

        return
