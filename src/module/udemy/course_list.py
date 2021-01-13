#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep

import urllib3
from tqdm import tqdm

from module.udemy.base import UdemyBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class UdemyCourseList(UdemyBase):

    def __init__(self, params):
        super().__init__(params=params)

    def batch(self):
        """강좌 목록을 다운로드 받는다."""
        self.logger.log(msg={
            'MESSAGE': '코스 목록 조회'
        })

        result = []
        for page in tqdm(range(1, self.params.max_page + 1), desc='course list'):
            self.selenium.reset_requests()

            url = 'https://ncsoft.udemy.com/home/my-courses/learning/?p={page}'.format(page=page)

            self.selenium.open(url=url)
            sleep(self.params.sleep)

            resp = self.selenium.get_requests(resp_url_path='/api-2.0/users/me/subscribed-courses/')
            if len(resp) == 0:
                break

            is_stop = False
            for r in resp:
                if 'results' not in r.data:
                    is_stop = True
                    break

                corpus_list = r.data['results']
                result += corpus_list

                self.save_cache(cache=result, path=self.params.data_path, name='course_list')

            if is_stop is True:
                break

        self.save_cache(cache=result, path=self.params.data_path, name='course_list', save_time_tag=True)

        return
