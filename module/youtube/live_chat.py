#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from utils import Logger
from utils import SeleniumWireUtils
from module.youtube.cache_utils import CacheUtils


class YoutubeLiveChat(object):

    def __init__(self, params):
        super().__init__()

        self.params = params

        self.logger = Logger()

        self.selenium = SeleniumWireUtils(headless=True)

        self.db = CacheUtils(filename=self.params.filename)
        self.db.use_cache = self.params.use_cache

    def get_live_chat(self):
        sql = 'SELECT id, title FROM videos'
        self.db.cursor.execute(sql)

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            v_id = item[0]
            title = item[1]

            v_id = 's5kHF08Sqi4'

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '라이브 채팅 조회',
                'video id': v_id,
                'title': title,
                'position': i,
                'size': len(rows)
            })

            url = 'https://www.youtube.com/watch?v={v_id}'.format(v_id=v_id)
            self.selenium.open(
                url=url,
                resp_url_path=None,
                wait_for_path=None
            )

            init_data = self.selenium.driver.execute_script('return window["ytInitialData"]')

            for x in self.selenium.get_requests(resp_url_path='/get_live_chat_replay'):
                pass

        return
