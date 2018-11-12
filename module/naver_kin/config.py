#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class Config(object):
    """"""

    def __init__(self):
        """ 생성자 """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        self.job_info = {}
        with open('schedule/jobs/naver_kin_crawler.json', 'r') as fp:
            str_doc = ''.join(fp.readlines())
            self.job_info = json.loads(str_doc)

        self.parsing_info = []
        with open('schedule/parsing/naver_kin_crawler.json', 'r') as fp:
            str_doc = ''.join(fp.readlines())
            self.parsing_info = json.loads(str_doc)
