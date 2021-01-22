#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep
from urllib.parse import urljoin

import requests
from tqdm.autonotebook import tqdm
from datetime import datetime
from bs4 import BeautifulSoup

from crawler.utils.elasticsearch_utils import ElasticSearchUtils
from crawler.utils.selenium_utils import SeleniumProxyUtils


class YahooTWCrawler(SeleniumProxyUtils):
    """유튜브 라이브 채팅 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.home_path = 'data/yahoo-tw'
        self.data_path = self.home_path

        host = 'https://crawler:crawler2019@corpus.ncsoft.com:9200'
        index = 'crawler-yahoo-tw'

        self.elastic = ElasticSearchUtils(host=host, index=index, split_index=True)

    def get_contents(self, doc):
        """ """
        if doc['url'][0] == '/':
            url = 'https://tw.news.yahoo.com/'
            doc['url'] = urljoin(url, doc['url'])

        try:
            self.driver.get(doc['url'].strip())
            self.driver.implicitly_wait(30)

            sleep(3)
        except Exception as e:
            print({'error at get_contents', e})
            return

        try:
            html = self.driver.page_source

            soup = BeautifulSoup(html, 'html5lib')

            tag_list = soup.find_all('article')
            if len(tag_list) > 0:
                doc['html_content'] = '\n'.join([v.prettify() for v in tag_list])
                doc['content'] = '\n'.join([v.get_text(separator='\n').strip() for v in tag_list])

                self.elastic.save_document(document=doc, delete=False)
                self.elastic.flush()
        except Exception as e:
            print({'error at get_contents', e})

        # self.page_down(count=30)
        # self.trace_networks()
        return

    def trace_contents(self):
        """모든 컨텐츠를 수집한다."""
        query = {
            'query': {
                'bool': {
                    'must_not': {
                        'exists': {
                            'field': 'html_content'
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

        self.open_driver()
        self.driver.implicitly_wait(10)

        while start < len(id_list):
            doc_list = []
            self.elastic.get_by_ids(id_list=id_list[start:end], index=self.elastic.index, source=None, result=doc_list)

            if start >= len(id_list):
                break

            start = end
            end += size

            if end > len(id_list):
                end = len(id_list)

            pbar = tqdm(doc_list, desc='{:,}~{:,}'.format(start, end))
            for doc in pbar:
                if 'html_content' in doc and doc['html_content'] == '':
                    continue

                self.get_contents(doc=doc)
                sleep(5)

        self.close_driver()

        return

    def get_url_list(self, url_list):
        """ """
        doc_list = []

        pbar = tqdm(url_list)
        for url in pbar:
            if url in self.url_buf:
                continue

            self.url_buf[url] = 1

            resp = None
            try:
                resp = requests.get(url, headers=self.headers, verify=False)
                resp = resp.json()
            except Exception as e:
                print({'get url error', url, resp.text, e})
                continue

            if 'data' not in resp:
                continue

            if 'items' in resp['data']:
                item_list = resp['data']['items']
            else:
                item_list = resp['data']

            new_list = []
            for item in item_list:
                if 'rows' not in item:
                    continue

                new_list += item['rows']

            if len(new_list) > 0:
                item_list = new_list

            if isinstance(item_list, list) is not True:
                continue

            try:
                for item in item_list:
                    if 'rows' in item:
                        item = item['rows']

                    doc = {}
                    for k in ['title', 'summary', 'tags', 'url', 'type', 'published_at', 'provider_name', 'author_name',
                              'author_alias', 'author_display_name']:
                        if k not in item:
                            continue

                        doc[k] = item[k]

                    if 'uuid' in item:
                        doc['_id'] = item['uuid']

                    if 'id' in item:
                        doc['_id'] = item['id']

                    if 'url' not in doc:
                        continue

                    doc['url'] = urljoin(url, item['url'])
                    doc['curl_date'] = datetime.now(self.timezone).isoformat()

                    if doc['url'].find('bit.ly') > 0:
                        doc['url'] = requests.head(doc['url']).headers['location']

                    if doc['url'].find('-') > 0:
                        doc['_id'] += '-' + doc['url'].replace('.html', '').rsplit('-', maxsplit=1)[-1]
                    elif doc['url'].find('/vod/') > 0:
                        url_info = self.parse_url(doc['url'])
                        if 'id' in url_info:
                            doc['_id'] += '-' + url_info['id']

                    doc_list.append(doc)

                    self.elastic.save_document(document=doc, delete=False)

                self.elastic.flush()
            except Exception as e:
                print({'get url error', e})

            sleep(5)

        return doc_list

    def trace_networks(self):
        """ """
        self.make_path(self.data_path)

        url_list = []
        for ent in self.proxy.har['log']['entries']:
            url = ent['request']['url']

            if url.find('/api/resource') < 0:
                continue

            if url.find('/api/resource/lang') > 0 or url.find('/api/resource/config') > 0:
                continue

            if url in self.url_buf:
                continue

            url_list.append(url)

        if len(url_list) == 0:
            return True

        try:
            _ = self.get_url_list(url_list=url_list)
        except Exception as e:
            print({'error trace networks', e})

        return False

    def trace_list(self):
        """ """
        self.open_driver()
        self.driver.implicitly_wait(10)

        self.home_path = 'data/yahoo-tw'
        url_list = '''
            https://tw.news.yahoo.com/politics
            https://tw.news.yahoo.com/society
            https://tw.news.yahoo.com/sports
            https://tw.news.yahoo.com/technology
            https://tw.news.yahoo.com/finance
            https://tw.news.yahoo.com/archive
            https://tw.news.yahoo.com/world        
            https://tw.news.yahoo.com/health
            https://tw.news.yahoo.com/entertainment
            https://tw.news.yahoo.com/lifestyle
            https://tw.news.yahoo.com/tv-radio
            https://tw.news.yahoo.com/video
            https://tw.news.yahoo.com/weather/
            https://tw.news.yahoo.com/celebrity
            https://tw.news.yahoo.com/jp-kr
            https://tw.news.yahoo.com/music
            https://tw.news.yahoo.com/myfollow
        '''.strip().split('\n')

        for url in url_list:
            url = url.strip()

            for i in range(20):
                print({'url': url})

                try:
                    self.driver.get(url)
                    self.driver.implicitly_wait(60)
                except Exception as e:
                    print({'error', url, e})
                    break

                stop = self.page_down(count=10)
                if stop is True:
                    break

                stop = self.trace_networks()
                if stop is True:
                    break

            sleep(60 * 1)

        self.close_driver()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--user_data', default=None, help='')
        parser.add_argument('--use_head', action='store_false', default=True, help='')

        parser.add_argument('--list', action='store_true', default=False, help='')
        parser.add_argument('--contents', action='store_true', default=False, help='')

        parser.add_argument('--proxy_server', default='module/browsermob-proxy/bin/browsermob-proxy', help='')

        return parser.parse_args()

    def batch(self):
        """ """
        self.args = self.init_arguments()

        for _ in range(10000):
            if self.args.list is True:
                self.trace_list()

            if self.args.contents is True:
                self.trace_contents()

            sleep(60 * 10)

        return


if __name__ == '__main__':
    utils = YahooTWCrawler()

    utils.batch()
