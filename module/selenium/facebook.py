#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
from datetime import datetime
from urllib.parse import urljoin
from time import sleep
import pytz
from bs4 import BeautifulSoup
from tqdm import tqdm
from dateutil.parser import parse as parse_date

from module.elasticsearch_utils import ElasticSearchUtils
from module.selenium.selenium_utils import SeleniumUtils

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging.basicConfig(
    format="[%(levelname)-s] %(message)s",
    handlers=[logging.StreamHandler()],
    level=MESSAGE,
)


class SeleniumCrawler(SeleniumUtils):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.max_try = 20

        host = 'https://crawler:crawler2019@corpus.ncsoft.com:9200'
        index = 'crawler-facebook'

        self.elastic = ElasticSearchUtils(host=host, index=index, split_index=True)

        self.timezone = pytz.timezone('Asia/Seoul')

        self.use_see_more_link = True

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
            post['html_content'] = '\n'.join([v.prettify() for v in tag.find_all('span', {'data-sigil': 'expose'})])

            post['content'] = '\n'.join([v.get_text(separator='\n') for v in tag.find_all('span', {'data-sigil': 'expose'})])

            # 공감 정보
            post['reactions'] = [str(v) for v in tag.find_all('div', {'data-sigil': 'reactions-sentence-container'})]

            post['url'] = [urljoin(url, v['href']) for v in tag.find_all('a', {'data-sigil': 'feed-ufi-trigger'}) if v.has_attr('href')]
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
            print({'delete_post', e})
            return None

        self.driver.implicitly_wait(10)

        return

    def save_post_list(self, post_list, group_info):
        """추출한 정보를 저장한다."""
        for doc in post_list:
            doc.update(group_info)
            if 'page' not in doc or 'top_level_post_id' not in doc:
                continue

            doc['_id'] = '{page}-{top_level_post_id}'.format(**doc)

            doc['category'] = group_info['category']
            doc['group_name'] = group_info['name']

            doc['curl_date'] = datetime.now(self.timezone).isoformat()

            self.elastic.save_document(document=doc, delete=False)

        self.elastic.flush()

        return

    def save_reply(self, doc, flush=True):
        """추출한 정보를 저장한다."""
        doc['_id'] = '{page}-{top_level_post_id}'.format(**doc)

        doc['curl_date'] = datetime.now(self.timezone).isoformat()

        self.elastic.save_document(document=doc, delete=False)
        if flush is True:
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

        story_body = soup.find_all('div', {'class': 'story_body_container'})

        doc['html_content'] = '\n'.join([v.prettify() for v in story_body])
        doc['content'] = '\n'.join([v.get_text(separator='\n') for v in soup.find_all('p')])

        return

    def see_more_reply(self):
        """ 더 보기 링크를019! 클릭한다."""
        self.max_try = 15
        self.see_prev_reply()

        try:
            ele_list = self.driver.find_elements_by_tag_name('a')
            for ele in ele_list:
                if ele.text.find('답글') < 0 or ele.text.find('개') < 0:
                    continue

                ele.click()
                self.driver.implicitly_wait(15)
                sleep(2)
        except Exception as e:
            print({'more reply error: ', e})

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
                if ele.text.find('이전 댓글 보기') < 0:
                    continue

                stop = False

                ele.click()
                self.driver.implicitly_wait(15)
                sleep(2)
        except NoSuchElementException:
            return
        except Exception as e:
            print({'see prev reply error: ', e})
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
                    },
                    'must_not': {
                        'exists': {
                            'field': 'reply_list'
                        }
                    }
                }
            }
        }

        id_list = self.elastic.get_id_list(index=self.elastic.index, query_cond=query)
        id_list = list(id_list)

        if len(id_list) == 0:
            return

        size = 1000

        start = 0
        end = size

        while start < len(id_list):
            doc_list = []
            self.elastic.get_by_ids(id_list=id_list[start:end], index=self.elastic.index, source=None, result=doc_list)

            if start >= len(id_list):
                break

            start = end
            end += size

            if end > len(id_list):
                end = len(id_list)

            self.open_driver()

            pbar = tqdm(doc_list, desc='{} {:,}~{:,}'.format(group_info['name'], start, end))
            for doc in pbar:
                pbar.set_description(group_info['name'] + ' ' + str(doc['top_level_post_id']))

                self.get_reply(doc=doc)

                self.save_reply(doc=doc)
                sleep(5)

            self.close_driver()

        return

    def trace_post_list(self, group_info):
        """하나의 계정을 모두 읽어드린다."""
        self.open_driver()

        url = '{site}/{page}'.format(**group_info)

        self.use_see_more_link = False

        self.driver.get(url)
        self.driver.implicitly_wait(10)

        for _ in tqdm(range(50000)):
            stop = self.page_down(count=10)
            self.driver.implicitly_wait(25)

            try:
                post_list = self.parse_post(url=url, html=self.driver.page_source)
            except Exception as e:
                print('get page error: ', e)
                continue

            if post_list is None or len(post_list) == 0:
                break

            self.save_post_list(post_list=post_list, group_info=group_info)

            # 태그 삭제
            self.delete_post()

            if stop is True:
                break

        self.close_driver()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-list', action='store_true', default=False, help='')
        parser.add_argument('-reply', action='store_true', default=False, help='')

        parser.add_argument('-config', default='./config/fb.page.list.json', help='')
        parser.add_argument('-user_data', default='./cache/selenium/facebook', help='')

        parser.add_argument('-use_head', action='store_false', default=True, help='')

        return parser.parse_args()


if __name__ == '__main__':
    # https://stackabuse.com/getting-started-with-selenium-and-python/

    utils = SeleniumCrawler()

    utils.args = utils.init_arguments()

    group_list = utils.read_config(filename=utils.args.config)

    for group in group_list:
        if utils.args.list:
            utils.trace_post_list(group_info=group)

    for group in group_list:
        if utils.args.reply:
            utils.trace_reply_list(group_info=group)
