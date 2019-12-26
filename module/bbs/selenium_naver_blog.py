#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import os
from time import sleep
from urllib.parse import urljoin
from urllib.parse import urlparse, parse_qs
from datetime import datetime

import pytz
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from selenium import webdriver
from tqdm import tqdm

from module.elasticsearch_utils import ElasticSearchUtils

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging.basicConfig(
    level=MESSAGE,
    format="[%(levelname)-s] %(message)s",
    handlers=[logging.StreamHandler()],
)


class SeleniumCrawler(object):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.driver = None

        path = os.path.dirname(os.path.realpath(__file__))
        self.driver_path = '{pwd}/../chromedriver'.format(pwd=path)

        host = 'https://crawler:crawler2019@corpus.ncsoft.com:9200'
        index = 'crawler-bbs-naver'

        self.elastic = ElasticSearchUtils(host=host, index=index, split_index=True)

        self.timezone = pytz.timezone('Asia/Seoul')

    def open_driver(self):
        """브라우저를 실행한다."""
        options = webdriver.ChromeOptions()

        options.add_argument('headless')
        options.add_argument('window-size=1000x800')
        options.add_argument("disable-gpu")

        options.add_argument('--dns-prefetch-disable')
        options.add_argument('disable-infobars')
        options.add_argument('user-data-dir=selenium-data')

        options.add_experimental_option('prefs', {
            'disk-cache-size': 4096,
            'profile.managed_default_content_settings.images': 2,
        })

        return webdriver.Chrome(self.driver_path, chrome_options=options)

    def scroll(self, count):
        """스크롤한다."""
        from selenium.webdriver.support.ui import WebDriverWait

        def check_height(prev_height):
            """현재 위치를 확인한다."""
            h = self.driver.execute_script("return document.body.scrollHeight")
            return h != prev_height

        scroll_time = 5
        last_height = -1

        for _ in range(count):
            try:
                height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.driver.implicitly_wait(5)

                WebDriverWait(self.driver, scroll_time, 0.1).until(lambda x: check_height(height))
            except Exception as e:
                print('scroll error: ', e)
                break

            if last_height == height:
                return True

            last_height = height
            sleep(5)

        return False

    def save_list(self, page_list, cafe_name):
        """추출한 정보를 저장한다."""
        for doc in page_list:
            url = self.parse_url(url=doc['url'])

            doc['_id'] = datetime.now(self.timezone).strftime('%Y%m%d-%H%M%S')
            if 'blogId' in url and 'logNo' in url:
                doc['_id'] = '{blogId}-{logNo}'.format(**url)

            doc['blog_name'] = cafe_name
            doc['curl_date'] = datetime.now(self.timezone).isoformat()

            self.elastic.save_document(document=doc, delete=False)

        self.elastic.flush()

        return

    def save_contents(self, doc, cafe_name):
        """추출한 정보를 저장한다."""
        url = self.parse_url(url=doc['url'])
        doc['_id'] = '{blogId}-{logNo}'.format(**url)

        doc['blog_name'] = cafe_name
        doc['curl_date'] = datetime.now(self.timezone).isoformat()

        self.elastic.save_document(document=doc, delete=False)
        self.elastic.flush()

        return

    @staticmethod
    def parse_url(url):
        """url 에서 쿼리문을 반환한다."""
        url_info = urlparse(url)
        query = parse_qs(url_info.query)
        for key in query:
            query[key] = query[key][0]

        return query

    def delete_post(self):
        """태그 삭제"""
        script = 'document.querySelectorAll("div.item").forEach(function(ele) {ele.remove();})'

        try:
            self.driver.execute_script(script)
        except Exception as e:
            print(e, flush=True)
            return None

        self.driver.implicitly_wait(10)

        return

    @staticmethod
    def get_page_list(url, html):
        """포스트 내용을 추출한다."""
        soup = BeautifulSoup(html, 'html5lib')

        tag_list = soup.select('div.wrap_postlist div.item')

        result = []
        for box in tag_list:
            post = dict()

            post['title'] = ''.join([v.get_text().strip() for v in box.select('div.area_text strong.title.ell')])

            post['replay_count'] = ''.join([v.get_text().strip() for v in box.select('div.meta_foot span.reply')]).replace('댓글', '').strip()

            post['url'] = urljoin(url, [v['href'] for v in box.select('a.link') if v.has_attr('href')][0])

            result.append(post)

        return result

    @staticmethod
    def replace_tag(html_tag, tag_list, replacement='', attribute=None):
        """ html 태그 중 특정 태그를 삭제한다. ex) script, caption, style, ... """
        if html_tag is None:
            return False

        for tag_name in tag_list:
            for tag in html_tag.find_all(tag_name, attrs=attribute):
                if replacement == '':
                    tag.extract()
                else:
                    tag.replace_with(replacement)

        return True

    def get_contents(self, item):
        """컨텐츠 하나를 조회한다."""
        if self.driver is None:
            self.driver = self.open_driver()

        self.driver.get(item['url'])
        self.driver.implicitly_wait(3)

        html = self.driver.page_source

        soup = BeautifulSoup(html, 'html5lib')

        item['category'] = ''.join([v.get_text().strip() for v in soup.select('strong.tit_category')])
        item['title'] = ''.join([v.get_text().strip() for v in soup.select('div.tit_area h3.tit_h3')])

        dt = ''.join([v.get_text().strip() for v in soup.select('div.author_area > p.se_date')])
        if dt != '':
            item['date'] = parse_date(dt).astimezone(self.timezone).isoformat()

        item['image'] = []
        item['content'] = ''
        item['html_content'] = ''

        for content in soup.select('div._postView div#viewTypeSelector'):
            item['image'] += [v['src'] for v in content.find_all('img') if v.has_attr('src')]

            item['content'] += content.get_text().strip()
            item['html_content'] += content.prettify()

        self.replace_tag(soup, ['script', 'javascript'])

        item['raw_html'] = soup.prettify()

        return

    def trace_contents(self, bbs_info):
        """모든 컨텐츠를 수집한다."""
        query = {
            'sort': [{
                'date': 'desc'
            }],
            'query': {
                'bool': {
                    'must': {
                        'match': {
                            'blog_name': bbs_info['name']
                        }
                    },
                    # 'must_not': {
                    #     'exists': {
                    #         'field': 'html_content'
                    #     }
                    # }
                }
            }
        }

        id_list = self.elastic.get_id_list(index=self.elastic.index, query_cond=query)

        bbs_list = []
        self.elastic.get_by_ids(id_list=list(id_list), index=self.elastic.index, source=None, result=bbs_list)

        if self.driver is None:
            self.driver = self.open_driver()

        for item in tqdm(bbs_list):
            self.get_contents(item=item)

            self.save_contents(doc=item, cafe_name=bbs_info['name'])
            sleep(5)

        self.driver.quit()
        self.driver = None

        return

    def get_contents_list(self, bbs_info, max_iter=2):
        """하나의 계정을 모두 읽어드린다."""
        if self.driver is None:
            self.driver = self.open_driver()

        self.driver.get(bbs_info['url'])
        self.driver.implicitly_wait(10)

        for _ in tqdm(range(max_iter)):
            self.scroll(count=2)
            self.driver.implicitly_wait(5)

            try:
                page_list = self.get_page_list(url=bbs_info['url'], html=self.driver.page_source)
            except Exception as e:
                print('get page error: ', e)
                continue

            if page_list is None or len(page_list) == 0:
                break

            self.save_list(page_list=page_list, cafe_name=bbs_info['name'])

            # 태그 삭제
            self.delete_post()

        self.driver.quit()
        self.driver = None

        return

    @staticmethod
    def read_config(filename='./naver.bbs.list.json'):
        """설정파일을 읽어드린다."""
        result = []

        with open(filename, 'r') as fp:
            buf = ''
            for line in fp.readlines():
                line = line.strip()
                if line.strip() == '' or line[0:2] == '//' or line[0] == '#':
                    continue

                buf += line
                if line != '}':
                    continue

                doc = json.loads(buf)
                buf = ''

                result.append(doc)

        return result

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-config', default='./naver.blog.list.json', help='')

        parser.add_argument('-list', action='store_true', default=False, help='')
        parser.add_argument('-contents', action='store_true', default=False, help='')

        parser.add_argument('-name', default=None, help='')

        return parser.parse_args()


def main():
    """"""
    # https://stackabuse.com/getting-started-with-selenium-and-python/
    utils = SeleniumCrawler()

    args = utils.init_arguments()

    bbs_list = utils.read_config(filename=args.config)

    pbar = tqdm(bbs_list)
    for bbs in pbar:
        if args.name is not None and args.name != bbs['name']:
            continue

        if args.list:
            pbar.set_description(bbs['name'] + ' list')

            utils.get_contents_list(bbs_info=bbs, max_iter=bbs['max_page'])

        if args.contents:
            pbar.set_description(bbs['name'] + ' contents')

            utils.trace_contents(bbs_info=bbs)

    return


if __name__ == '__main__':
    main()
