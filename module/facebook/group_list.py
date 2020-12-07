#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from module.facebook.base import FBBase


class FBGroupList(FBBase):

    def __init__(self, params):
        super().__init__(params=params)

        self.params = params

    def trace_post_list(self, group_info):
        """하나의 계정을 모두 읽어드린다."""
        self.selenium.open_driver()

        url = '{site}/{page}'.format(**group_info)

        self.selenium.driver.get(url)
        self.selenium.driver.implicitly_wait(10)

        i = 0
        for _ in range(self.params.max_page):
            stop = self.selenium.page_down(count=10)
            self.selenium.driver.implicitly_wait(25)

            i += 1

            try:
                post_list = self.parser.parse_post(url=url, html=self.selenium.driver.page_source)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'post 목록 조회 에러',
                    'exception': str(e),
                })
                continue

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'trace post list',
                'page': '{:,}/{:,}'.format(i, self.params.max_page),
                'count_post_list': len(post_list),
            })

            if post_list is None or len(post_list) == 0:
                break

            for doc in post_list:
                self.save_post(doc=doc, group_info=group_info)

            if self.elastic is not None:
                self.elastic.flush()

            # 태그 삭제
            self.delete_post()

            if stop is True:
                break

        self.selenium.close_driver()

        return

    def delete_post(self):
        """이전 포스트를 삭제한다."""
        script = 'document.querySelectorAll("article").forEach(function(ele) {ele.remove();})'

        try:
            self.selenium.driver.execute_script(script)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'delete post',
                'exception': str(e),
            })
            return None

        self.selenium.driver.implicitly_wait(10)

        return

    def batch(self):
        group_list = self.read_config(filename=self.params.config)

        for group in group_list:
            self.trace_post_list(group_info=group)

        return
