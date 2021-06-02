#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from base64 import decodebytes
from datetime import datetime
from time import sleep

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException

from crawler.facebook.core import FacebookCore
from crawler.utils.es import ElasticSearchUtils
from crawler.utils.selenium import SeleniumUtils


class FacebookReplies(FacebookCore):

    def __init__(self, params: dict):
        super().__init__(params=params)

    def get_replies(self, post: dict, job: dict) -> int:
        """컨텐츠 하나를 조회한다."""
        if 'url' not in post:
            return -1

        self.selenium.open_driver()

        self.selenium.driver.get(post['url'])
        self.selenium.driver.implicitly_wait(15)

        self.see_more_reply()

        dt = datetime.now(self.timezone).isoformat()
        soup = BeautifulSoup(self.selenium.driver.page_source, 'html5lib')

        count = 0
        for tag in soup.find_all('div', {'data-sigil': 'comment'}):
            comment_list = tag.find_all('div', {'data-sigil': 'comment-body'})
            for item in comment_list:
                count += 1

                doc = {
                    '@crawl_date': dt,
                    'raw': str(item),
                    **{k: v for k, v in post.items() if k[0] != '_'},
                    **json.loads(tag['data-store']),
                    **self.parser.parse_reply_body(item)
                }

                doc['_id'] = f'''{post['top_level_post_id']}-{doc['reply_id']}'''

                if 'token' in doc:
                    del doc['token']

                self.es.save_document(document=doc, delete=False, index=job['index']['reply'])

        self.es.flush()

        return count

    def see_more_reply(self) -> None:
        """ 더 보기 링크를 클릭한다."""
        self.see_prev_reply(max_try=self.params['max_try'])

        try:
            ele_list = self.selenium.driver.find_elements_by_tag_name('a')
            for ele in ele_list:
                href = ele.get_attribute('href')
                if href is None or href.find('/comment/replies/') < 0:
                    continue

                sigil = ele.get_attribute('data-sigil')
                if sigil != 'ajaxify':
                    continue

                ele.click()
                self.selenium.driver.implicitly_wait(15)
                sleep(2)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'more reply error',
                'exception': str(e),
            })

        sleep(2)
        return

    def see_prev_reply(self, max_try: int = 200) -> None:
        """ 이전 댓글 보기를 클릭한다."""
        if max_try < 0:
            return

        stop = True
        try:
            ele_list = self.selenium.driver.find_elements_by_tag_name('a')
            for ele in ele_list:
                href = ele.get_attribute('href')

                if href is None or href.find('/story.php?story_fbid=') < 0:
                    continue

                sigil = ele.get_attribute('data-sigil')
                if sigil != 'ajaxify':
                    continue

                stop = False

                ele.click()
                self.selenium.driver.implicitly_wait(15)
                sleep(2)
        except NoSuchElementException:
            return
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'see prev reply error',
                'exception': str(e),
            })
            return

        if stop is True:
            return

        self.see_prev_reply(max_try=max_try - 1)
        return

    def get_post_list(self, page: str, limit: int = 100) -> list:
        query = {
            '_source': ['page', 'url', 'top_level_post_id', 'lang_code', 'category'],
            'track_total_hits': True,
            'query': {
                'bool': {
                    'must': [{
                        'match': {
                            'page': page
                        }
                    }, {
                        'match': {
                            'reply_count': -1
                        }
                    }]
                }
            }
        }

        result = []
        self.es.dump_index(index=self.config['index']['post'], limit=limit, query=query, size=limit, result=result)

        return result

    def update_post(self, index: str, post_id: str, count: int) -> None:
        self.es.conn.update(
            index=index,
            id=post_id,
            body={
                'doc': {
                    'reply_count': count
                }
            },
            refresh=True,
        )

        return

    def batch(self) -> None:
        self.config = self.read_config(filename=self.params['config'])

        self.es = ElasticSearchUtils(
            host=self.params['host'],
            http_auth=decodebytes(self.params['auth_encoded'].encode('utf-8')).decode('utf-8')
        )

        self.create_index(index=self.config['index']['page'])
        self.create_index(index=self.config['index']['reply'])

        self.selenium = SeleniumUtils(
            login=self.params['login'],
            headless=self.params['headless'],
            user_data_path=self.params['user_data'],
        )

        for job in self.config['jobs']:
            post_list = self.get_post_list(page=job['page'], limit=100)

            while len(post_list) > 0:
                for post in post_list:
                    count = self.get_replies(post=post, job=job)

                    self.update_post(index=self.config['index']['post'], post_id=post['_id'], count=count)

                post_list = self.get_post_list(page=job['page'], limit=100)

        return
