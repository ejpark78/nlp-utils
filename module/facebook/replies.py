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

from module.facebook.base import FBBase


class FBReplies(FBBase):

    def __init__(self, params):
        super().__init__(params=params)

        self.params = params

    def save_reply(self, reply_list, post_id, index):
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

            self.elastic.save_document(document=doc, delete=False, index=index)

            if 'reply_list' in reply:
                self.save_reply(reply_list=reply['reply_list'], post_id=post_id, index=index)

        self.elastic.flush()

        return

    def get_reply(self, doc):
        """컨텐츠 하나를 조회한다."""
        if 'url' not in doc:
            return

        self.selenium.open_driver()

        self.selenium.driver.get(doc['url'])
        self.selenium.driver.implicitly_wait(15)

        self.see_more_reply()

        html = self.selenium.driver.page_source

        soup = BeautifulSoup(html, 'html5lib')

        reply_list = []
        for tag in soup.find_all('div', {'data-sigil': 'comment'}):
            item = dict()

            item.update(json.loads(tag['data-store']))

            item['data-uniqueid'] = tag['data-uniqueid']

            comment_list = tag.find_all('div', {'data-sigil': 'comment-body'})
            replies = [self.parser.parse_reply_body(v) for v in comment_list]
            if len(replies) > 0:
                item.update(replies[0])
                del replies[0]

            item['reply_list'] = replies

            reply_list.append(item)

        doc['reply_list'] = reply_list

        doc['content'] = '\n'.join([v.get_text(separator='\n') for v in soup.find_all('p')])

        story_body = soup.find_all('div', {'class': 'story_body_container'})
        doc['html_content'] = '\n'.join([v.prettify() for v in story_body])

        return

    def see_more_reply(self):
        """ 더 보기 링크를019! 클릭한다."""
        self.params.max_try = 15
        self.see_prev_reply()

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

    def see_prev_reply(self):
        """ 이전 댓글 보기를 클릭한다."""
        self.params.max_try -= 1
        if self.params.max_try < 0:
            self.params.max_try = 15
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
            self.params.max_try = 15
            return

        self.see_prev_reply()
        return

    def trace_reply_list(self, group_info):
        query = {
            'query': {
                'bool': {
                    'must': {
                        'match': {
                            'page': group_info['page']
                        }
                    }
                }
            }
        }

        if self.params.overwrite is False:
            query['query']['bool']['must_not'] = {
                'match': {
                    'state': 'done'
                }
            }

        id_list = self.elastic.get_id_list(index=self.elastic.index, query_cond=query)
        id_list = list(id_list)

        if len(id_list) == 0:
            return

        size = 1000

        start = 0
        end = size

        if 'index' in group_info:
            self.params.index = group_info['index']
            self.elastic.index = group_info['index']

        reply_index = self.params.reply_index
        if 'reply_index' in group_info:
            self.params.reply_index = group_info['reply_index']

        while start < len(id_list):
            doc_list = []
            self.elastic.get_by_ids(
                index=self.elastic.index,
                source=None,
                result=doc_list,
                id_list=id_list[start:end],
            )

            if start >= len(id_list):
                break

            start = end
            end += size

            if end > len(id_list):
                end = len(id_list)

            self.selenium.open_driver()

            for i, doc in enumerate(doc_list):
                if self.params.overwrite is False and 'reply_list' in doc:
                    continue

                self.logger.log({
                    'level': 'MESSAGE',
                    'message': 'trace_reply_list',
                    'name': group_info['meta']['name'],
                    'start': start,
                    'end': end,
                    'i': i,
                    'top_level_post_id': doc['top_level_post_id']
                })

                self.get_reply(doc=doc)

                if 'reply_list' in doc:
                    post_id = '{page}-{top_level_post_id}'.format(**doc)
                    self.save_reply(reply_list=doc['reply_list'], post_id=post_id, index=reply_index)

                    del doc['reply_list']

                    doc['state'] = 'done'
                    self.save_post(doc=doc, group_info=group_info)

                sleep(5)

            self.selenium.close_driver()

        return

    def batch(self):
        group_list = self.read_config(filename=self.params.config)

        for group in group_list:
            self.trace_reply_list(group_info=group)

        return
