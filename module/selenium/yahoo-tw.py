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

from module.elasticsearch_utils import ElasticSearchUtils
from module.selenium.proxy_utils import SeleniumProxyUtils


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

    def get_url_list(self, url_list):
        """ """
        pbar = tqdm(url_list)
        for url in pbar:
            if url in self.url_buf:
                continue

            self.url_buf[url] = 1

            resp = None
            try:
                resp = requests.get(url, headers=self.headers)
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

                    doc['url'] = urljoin(url, item['url'])
                    doc['curl_date'] = datetime.now(self.timezone).isoformat()

                    self.elastic.save_document(document=doc, delete=False)

                self.elastic.flush()
            except Exception as e:
                print('get url error', e)
                pass

            sleep(5)

        return

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
            self.get_url_list(url_list=url_list)
        except Exception as e:
            print('error trace networks', e)

        return False

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-user_data', default=None, help='')
        parser.add_argument('-use_head', action='store_false', default=True, help='')

        return parser.parse_args()

    def batch(self):
        """ """
        self.args = self.init_arguments()

        self.open_driver()

        self.home_path = 'data/yahoo-tw'
        url_list = '''
https://tw.news.yahoo.com/topic
https://tw.news.yahoo.com/tv-radio
https://tw.news.yahoo.com/video
https://tw.news.yahoo.com/weather/
https://tw.news.yahoo.com/world        
https://tw.news.yahoo.com/archive
https://tw.buy.yahoo.com/shopdaily/
https://tw.news.yahoo.com/blogs
https://tw.news.yahoo.com/celebrity
https://tw.news.yahoo.com/entertainment
https://tw.news.yahoo.com/finance
https://tw.news.yahoo.com/health
https://tw.news.yahoo.com/jp-kr
https://tw.news.yahoo.com/lifestyle
https://tw.news.yahoo.com/music
https://tw.news.yahoo.com/myfollow
https://tw.news.yahoo.com/politics
https://tw.news.yahoo.com/society
https://tw.news.yahoo.com/sports
https://tw.news.yahoo.com/technology
        '''.strip().split('\n')

        for url in url_list:
            for i in range(100):
                self.driver.get(url)
                self.driver.implicitly_wait(60)

                stop = self.page_down(count=5)
                if stop is True:
                    break

                stop = self.trace_networks()
                if stop is True:
                    break

            sleep(60 * 1)

        self.close_driver()

        return


if __name__ == '__main__':
    utils = YahooTWCrawler()

    utils.batch()
