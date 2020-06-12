#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from datetime import datetime
from time import sleep
from urllib.parse import urljoin

import pytz
from bs4 import BeautifulSoup

from module.utils.elasticsearch_utils import ElasticSearchUtils
from module.utils.logger import Logger
from module.utils.selenium_utils import SeleniumUtils


class SeleniumCrawler(SeleniumUtils):
    """페이스북 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.max_try = 20

        self.elastic = None

        self.timezone = pytz.timezone('Asia/Seoul')

        self.use_see_more_link = True

        self.logger = Logger()

    def open_db(self):
        """ """
        self.elastic = ElasticSearchUtils(
            host=self.env.host,
            index=self.env.index,
            http_auth=self.env.auth,
            split_index=True,
        )
        return

    @staticmethod
    def parse_post(url, html):
        """포스트 내용을 추출한다."""
        soup = BeautifulSoup(html, 'html5lib')

        tag_list = soup.find_all('article')

        result = []
        for tag in tag_list:
            post = dict()

            for k, v in tag.attrs.items():
                if k not in ['data-ft', 'data-store']:
                    continue

                attrs = json.loads(v)
                post.update(attrs)

            post['raw_html'] = tag.prettify()

            # 메세지 추출
            span_list = tag.find_all('span', {'data-sigil': 'more'})
            if len(span_list) > 0:
                post['content'] = '\n'.join([v.get_text(separator='\n') for v in span_list])
                post['html_content'] = '\n'.join([v.prettify() for v in span_list])
            else:
                post['content'] = '\n'.join([v.get_text(separator='\n') for v in tag.find_all('p')])

                story_body = tag.find_all('div', {'class': 'story_body_container'})
                post['html_content'] = '\n'.join([v.prettify() for v in story_body])

            # 공감 정보
            div_list = tag.find_all('div', {'data-sigil': 'reactions-sentence-container'})
            post['reactions'] = [str(v) for v in div_list]

            a_list = tag.find_all('a', {'data-sigil': 'feed-ufi-trigger'})
            post['url'] = [urljoin(url, v['href']) for v in a_list if v.has_attr('href')]
            if len(post['url']) > 0:
                post['url'] = post['url'][0]
            else:
                del post['url']

            result.append(post)

        return result

    def delete_post(self):
        """태그 삭제"""
        script = 'document.querySelectorAll("article").forEach(function(ele) {ele.remove();})'

        try:
            self.driver.execute_script(script)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'delete post',
                'exception': str(e),
            })
            return None

        self.driver.implicitly_wait(10)

        return

    def save_post(self, doc, group_info):
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
        self.elastic.save_document(document=doc, delete=False, index=index)

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '문서 저장 성공',
            'document_id': doc['document_id'],
            'content': doc['content'],
        })

        return

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

            self.elastic.save_document(document=doc, delete=False, index=index)

            if 'reply_list' in reply:
                self.save_reply(reply_list=reply['reply_list'], post_id=post_id, index=index)

        self.elastic.flush()

        return

    @staticmethod
    def parse_reply_body(tag):
        """ """
        raw_html = tag.prettify()

        user_name = ''
        for v in tag.parent.find_all('a'):
            if v['href'].find('/profile') is False:
                continue

            user_name = v.get_text()
            break

        reply_to = ''
        for v in tag.find_all('a'):
            if v['href'].find('/profile') is False:
                continue

            reply_to = v.get_text()
            v.extract()
            break

        result = {
            'user_name': user_name,
            'reply_to': reply_to,
            'reply_id': tag['data-commentid'],
            'text': tag.get_text(separator='\n'),
            'raw_html': raw_html,
        }

        return result

    def get_reply(self, doc):
        """컨텐츠 하나를 조회한다."""
        self.open_driver()

        self.driver.get(doc['url'])
        self.driver.implicitly_wait(15)

        self.see_more_reply()

        html = self.driver.page_source

        soup = BeautifulSoup(html, 'html5lib')

        reply_list = []
        for tag in soup.find_all('div', {'data-sigil': 'comment'}):
            item = dict()

            item.update(json.loads(tag['data-store']))

            item['data-uniqueid'] = tag['data-uniqueid']

            comment_list = tag.find_all('div', {'data-sigil': 'comment-body'})
            replies = [self.parse_reply_body(v) for v in comment_list]
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
        self.max_try = 15
        self.see_prev_reply()

        try:
            ele_list = self.driver.find_elements_by_tag_name('a')
            for ele in ele_list:
                href = ele.get_attribute('href')
                if href is None or href.find('/comment/replies/') < 0:
                    continue

                sigil = ele.get_attribute('data-sigil')
                if sigil != 'ajaxify':
                    continue

                ele.click()
                self.driver.implicitly_wait(15)
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
        from selenium.common.exceptions import NoSuchElementException

        self.max_try -= 1
        if self.max_try < 0:
            self.max_try = 15
            return

        stop = True
        try:
            ele_list = self.driver.find_elements_by_tag_name('a')
            for ele in ele_list:
                href = ele.get_attribute('href')

                if href is None or href.find('/story.php?story_fbid=') < 0:
                    continue

                sigil = ele.get_attribute('data-sigil')
                if sigil != 'ajaxify':
                    continue

                stop = False

                ele.click()
                self.driver.implicitly_wait(15)
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
            self.max_try = 15
            return

        self.see_prev_reply()
        return

    def trace_reply_list(self, group_info):
        """ """
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

        if self.env.overwrite is False:
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
            self.env.index = group_info['index']
            self.elastic.index = group_info['index']

        reply_index = self.env.reply_index
        if 'reply_index' in group_info:
            self.env.reply_index = group_info['reply_index']

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

            self.open_driver()

            for i, doc in enumerate(doc_list):
                if self.env.overwrite is False and 'reply_list' in doc:
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

            self.close_driver()

        return

    def trace_post_list(self, group_info):
        """하나의 계정을 모두 읽어드린다."""
        self.open_driver()

        url = '{site}/{page}'.format(**group_info)

        self.driver.get(url)
        self.driver.implicitly_wait(10)

        i = 0
        for _ in range(self.env.max_page):
            stop = self.page_down(count=10)
            self.driver.implicitly_wait(25)

            i += 1

            try:
                post_list = self.parse_post(url=url, html=self.driver.page_source)
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
                'page': '{:,}/{:,}'.format(i, self.env.max_page),
                'count_post_list': len(post_list),
            })

            if post_list is None or len(post_list) == 0:
                break

            for doc in post_list:
                self.save_post(doc=doc, group_info=group_info)
            self.elastic.flush()

            # 태그 삭제
            self.delete_post()

            if stop is True:
                break

        self.close_driver()

        return

    def sleep_to_login(self):
        """ """
        self.open_driver()

        self.driver.get('https://m.facebook.com')
        self.driver.implicitly_wait(10)

        sleep(3200)

        return

    def batch(self):
        """ """
        # https://stackabuse.com/getting-started-with-selenium-and-python/

        self.env = self.init_arguments()

        self.open_db()

        group_list = self.read_config(filename=self.env.config)

        if self.env.login:
            self.sleep_to_login()

        for group in group_list:
            if self.env.list:
                self.trace_post_list(group_info=group)

        for group in group_list:
            if self.env.reply:
                self.trace_reply_list(group_info=group)

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--login', action='store_true', default=False)

        parser.add_argument('--list', action='store_true', default=False)
        parser.add_argument('--reply', action='store_true', default=False)

        parser.add_argument('--overwrite', action='store_true', default=False)

        parser.add_argument('--config', default='./config/facebook/커뮤니티.json')
        parser.add_argument('--user_data', default=None)

        parser.add_argument('--use_head', action='store_false', default=True)
        parser.add_argument('--max_page', default=10000, type=int)

        parser.add_argument('--driver', default='/usr/lib/chromium-browser/chromedriver')

        parser.add_argument('--host', default='https://corpus.ncsoft.com:9200')
        parser.add_argument('--auth', default='crawler:crawler2019')
        parser.add_argument('--index', default='crawler-facebook')
        parser.add_argument('--reply_index', default='crawler-facebook-reply')

        return parser.parse_args()


if __name__ == '__main__':
    SeleniumCrawler().batch()
