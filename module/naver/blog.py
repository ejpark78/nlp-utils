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
from urllib.parse import urljoin
from urllib.parse import urlparse, parse_qs

import pytz
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from tqdm import tqdm

from utils.elasticsearch_utils import ElasticSearchUtils
from utils.selenium_utils import SeleniumUtils


class SeleniumCrawler(SeleniumUtils):
    """네이버 블로그 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.driver = None

        host = 'https://crawler:crawler2019@corpus.ncsoft.com:9200'
        index = 'crawler-naver-blog'

        self.elastic = ElasticSearchUtils(host=host, index=index, split_index=True)

        self.timezone = pytz.timezone('Asia/Seoul')

    def save_list(self, page_list, blog_name):
        """추출한 정보를 저장한다."""
        for doc in page_list:
            url = self.parse_url(url=doc['url'])

            doc['_id'] = datetime.now(self.timezone).strftime('%Y%m%d-%H%M%S')
            if 'blogId' in url and 'logNo' in url:
                doc['_id'] = '{blogId}-{logNo}'.format(**url)

            doc['blog_id'] = url['blogId']
            doc['blog_name'] = blog_name

            doc['curl_date'] = datetime.now(self.timezone).isoformat()

            self.elastic.save_document(document=doc, delete=False)

        self.elastic.flush()

        return

    def save_contents(self, doc, blog_name):
        """추출한 정보를 저장한다."""
        url = self.parse_url(url=doc['url'])
        doc['_id'] = '{blogId}-{logNo}'.format(**url)

        doc['blog_id'] = url['blogId']
        doc['blog_name'] = blog_name

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

        self.driver.implicitly_wait(10)

        return

    @staticmethod
    def get_page_list(url, html):
        """포스트 내용을 추출한다."""
        soup = BeautifulSoup(html, 'html5lib')

        post_list = soup.select('div.wrap_postlist div.item')

        result = []
        for box in post_list:
            post = dict()

            post['title'] = ''.join([v.get_text().strip() for v in box.select('div.area_text strong.title.ell')])

            post['replay_count'] = ''.join(
                [v.get_text().strip() for v in box.select('div.meta_foot span.reply')]).replace('댓글', '').strip()

            post['url'] = urljoin(url, [v['href'] for v in box.select('a.link') if v.has_attr('href')][0])

            result.append(post)

        return result

    def get_contents(self, item):
        """컨텐츠 하나를 조회한다."""
        self.open_driver()

        self.driver.get(item['url'])
        self.driver.implicitly_wait(15)

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

        item['files'] = [urljoin(item['url'], v['href']) for v in soup.select('div.files ul li a') if
                         v.has_attr('href')]

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
                    'must_not': {
                        'exists': {
                            'field': 'html_content'
                        }
                    }
                }
            }
        }

        id_list = self.elastic.get_id_list(index=self.elastic.index, query_cond=query)

        bbs_list = []
        self.elastic.get_by_ids(id_list=list(id_list), index=self.elastic.index, source=None, result=bbs_list)

        self.open_driver()

        for item in tqdm(bbs_list):
            self.get_contents(item=item)

            self.save_contents(doc=item, blog_name=bbs_info['name'])
            sleep(5)

        self.close_driver()

        return

    def get_contents_list(self, bbs_info, max_iter=2):
        """하나의 계정을 모두 읽어드린다."""
        self.open_driver()

        self.driver.get(bbs_info['url'])
        self.driver.implicitly_wait(10)

        self.wait_clickable(css='button.btn_list')

        sleep(15)
        btn = self.driver.find_element_by_css_selector('button.btn_list')
        if btn is not None:
            btn.click()

            self.driver.implicitly_wait(10)
            sleep(15)

        for _ in tqdm(range(max_iter)):
            self.page_down(count=2)
            self.driver.implicitly_wait(15)

            html = self.driver.page_source

            try:
                page_list = self.get_page_list(url=bbs_info['url'], html=html)
            except Exception as e:
                print('get page error: ', e)
                continue

            if page_list is None or len(page_list) == 0:
                break

            self.save_list(page_list=page_list, blog_name=bbs_info['name'])

            # 태그 삭제
            self.delete_post()

        self.close_driver()

        return

    @staticmethod
    def read_config(filename, with_comments=False):
        """설정파일을 읽어드린다."""
        file_list = filename.split(',')
        if isdir(filename) is True:
            file_list = []
            for f_name in glob('{}/*.json'.format(filename)):
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

    def batch(self):
        # https://stackabuse.com/getting-started-with-selenium-and-python/
        self.env = self.init_arguments()

        bbs_list = self.read_config(filename=self.env.config)

        pbar = tqdm(bbs_list)
        for bbs in pbar:
            if self.env.blogid is not None and self.env.blogid != bbs['blogId']:
                continue

            bbs['page'] = 1
            bbs['url'] = bbs['url'].format(**bbs)

            if self.env.list:
                pbar.set_description(bbs['name'] + ' list')

                bbs['max_page'] = 5000

                self.get_contents_list(bbs_info=bbs, max_iter=bbs['max_page'])

            if self.env.contents:
                pbar.set_description(bbs['name'] + ' contents')

                self.trace_contents(bbs_info=bbs)

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-config', default='./config/naver.blog.list.json', help='')
        parser.add_argument('-user_data', default='./cache/selenium/naver-blog', help='')

        parser.add_argument('-list', action='store_true', default=False, help='')
        parser.add_argument('-contents', action='store_true', default=False, help='')
        parser.add_argument('-c', action='store_true', default=False, help='')

        parser.add_argument('-use_head', action='store_false', default=True, help='')

        parser.add_argument('-blogid', default=None, help='')

        return parser.parse_args()


if __name__ == '__main__':
    SeleniumCrawler().batch()
