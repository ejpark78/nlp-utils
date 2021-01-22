#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import requests
import urllib3

from crawler.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class TedBase(object):

    def __init__(self, params):
        super().__init__()

        self.params = params
        self.logger = Logger()

        self.session = requests.Session()
        self.session.verify = False

        self.filename = {
            'url_list': 'data/ted/url-list.json',
            'talk_list': 'data/ted/talk-list.json',
        }

        self.page_url = 'https://www.ted.com/talks?page={page}'
        self.language_url = 'https://www.ted.com/talks/{talk_id}/transcript.json?language={languageCode}'

    def get_html(self, url):
        try:
            return self.session.get(url=url, verify=False, timeout=120)
        except Exception as e:
            self.logger.error({
                'ERROR': 'get_html',
                'url': url,
                'e': str(e),
            })

        return None
