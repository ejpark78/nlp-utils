#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from datetime import datetime
from glob import glob
from os.path import isdir
from time import sleep

from crawler.facebook.core import FacebookCore


class FacebookGroupList(FacebookCore):

    def __init__(self, params):
        super().__init__(params=params)

    def trace_post_list(self, group_info: dict) -> int:
        """하나의 계정을 조회한다."""
        self.selenium.open_driver()

        url = '{site}/{page}'.format(**group_info)

        self.selenium.driver.get(url)
        self.selenium.driver.implicitly_wait(10)

        i = 0
        count = 0

        for _ in range(self.params['max_page']):
            stop = self.selenium.page_down(count=10, sleep_time=3)
            self.selenium.driver.implicitly_wait(25)

            sleep(self.params['sleep'])
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

            count += len(post_list)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'trace post list',
                'page': f'''{i:,}/{self.params['max_page']:,}''',
                'count': f'{len(post_list):,}/{count:,}',
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

        return count

    def save_post(self, doc: dict, group_info: dict) -> None:
        """추출한 정보를 저장한다."""
        doc['page'] = group_info['page']
        if 'page' not in doc or 'top_level_post_id' not in doc:
            return

        doc['_id'] = '{page}-{top_level_post_id}'.format(**doc)

        if 'meta' in group_info:
            doc.update(group_info['meta'])

        doc['curl_date'] = datetime.now(self.timezone).isoformat()

        index = None
        if 'index' in group_info:
            index = group_info['index']

        if self.elastic is not None:
            self.elastic.save_document(document=doc, delete=False, index=index)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '문서 저장 성공',
                'document_id': doc['document_id'],
                'content': doc['content'],
            })

        if self.db is not None:
            self.db.save_post(document=doc, post_id=doc['top_level_post_id'])

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '문서 저장 성공',
                'group_info': group_info,
                'content': doc['content'],
            })

        return

    def delete_post(self) -> None:
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

    @staticmethod
    def read_config(filename: str, with_comments: bool = False) -> list:
        """설정파일을 읽어드린다."""
        file_list = filename.split(',')
        if isdir(filename) is True:
            file_list = []
            for f_name in glob(f'{filename}/*.json'):
                file_list.append(f_name)

        result = []
        for f_name in file_list:
            with open(f_name, 'r') as fp:
                if with_comments is True:
                    buf = ''.join([re.sub(r'^//', '', x) for x in fp.readlines()])
                else:
                    buf = ''.join([x for x in fp.readlines() if x.find('//') != 0])

                doc = json.loads(buf)
                result += doc['list']

        return result

    def account(self) -> None:
        account = self.read_config(filename=self.params['config'])

        for group in account:
            self.db.save_account(account_id=group['page'], name=group['meta']['name'], document=group)

        return

    def batch(self) -> None:
        group_list = self.read_config(filename=self.params['config'])

        for group in group_list:
            self.db.save_account(account_id=group['page'], name=group['meta']['name'], document=group)

            count = self.trace_post_list(group_info=group)
            self.db.save_post_count(account_id=group['page'], count=count)

        return
