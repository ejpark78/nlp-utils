#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from datetime import datetime
from time import sleep

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException

from .base import FBBase


class FBReplies(FBBase):

    def __init__(self, params):
        super().__init__(params=params)

        self.params = params

    def save_replies(self, reply_list, post_id, index):
        """추출한 정보를 저장한다."""
        if len(reply_list) == 0:
            return

        dt = datetime.now(self.timezone).isoformat()

        for reply in reply_list:
            doc = json.loads(json.dumps(reply))

            if 'token' in doc:
                del doc['token']

            if 'reply_list' in doc:
                del doc['reply_list']

            doc['_id'] = '{reply_id}'.format(**doc)
            doc['post_id'] = post_id
            doc['curl_date'] = dt

            doc = self.parser.to_string(doc=doc)

            if self.db is not None:
                self.db.save_replies(document=doc, post_id=post_id, reply_id=doc['reply_id'])

            if self.elastic is not None:
                self.elastic.save_document(document=doc, delete=False, index=index)

            if 'reply_list' in reply:
                self.save_replies(reply_list=reply['reply_list'], post_id=post_id, index=index)

        if self.elastic is not None:
            self.elastic.flush()

        return

    def get_replies(self, post):
        """컨텐츠 하나를 조회한다."""
        if 'url' not in post:
            return

        self.selenium.open_driver()

        self.selenium.driver.get(post['url'])
        self.selenium.driver.implicitly_wait(15)

        self.see_more_reply()

        html = self.selenium.driver.page_source

        soup = BeautifulSoup(html, 'html5lib')

        count = 0
        for tag in soup.find_all('div', {'data-sigil': 'comment'}):
            item = dict()

            item.update(json.loads(tag['data-store']))

            item['data-uniqueid'] = tag['data-uniqueid']

            comment_list = tag.find_all('div', {'data-sigil': 'comment-body'})
            replies = [self.parser.parse_reply_body(v) for v in comment_list]

            count += len(replies)
            for reply in replies:
                self.db.save_replies(document=reply, post_id=post['top_level_post_id'], reply_id=reply['reply_id'])

        post['content'] = '\n'.join([v.get_text(separator='\n') for v in soup.find_all('p')])

        story_body = soup.find_all('div', {'class': 'story_body_container'})
        post['html_content'] = '\n'.join([v.prettify() for v in story_body])

        self.db.save_post(document=post, post_id=post['top_level_post_id'])

        return count

    def see_more_reply(self):
        """ 더 보기 링크를 클릭한다."""
        self.see_prev_reply(max_try=self.params.max_try)

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

    def see_prev_reply(self, max_try=200):
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

    def batch(self):
        _ = self.db.cursor.execute('SELECT content FROM posts WHERE reply_count < 0')

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            post = json.loads(item[0])

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '댓글 조회',
                'content': post['content'],
                'position': f'{i:,}/{len(rows):,}',
            })

            count = self.get_replies(post=post)

            self.db.save_reply_count(post_id=post['top_level_post_id'], count=count)

        return
