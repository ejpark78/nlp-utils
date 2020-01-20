#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from datetime import datetime
from os import makedirs
from os.path import isdir, isfile, dirname
from time import sleep
from urllib.parse import unquote

import requests
from tqdm.autonotebook import tqdm

from module.elasticsearch_utils import ElasticSearchUtils
from module.selenium.proxy_utils import SeleniumProxyUtils


class YoutubeLiveChatCrawler(SeleniumProxyUtils):
    """유튜브 라이브 채팅 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.home_path = 'data/youtube-live-chat'
        self.data_path = self.home_path

        host = 'https://crawler:crawler2019@corpus.ncsoft.com:9200'
        index = 'crawler-youtube-live-chat'

        self.elastic = ElasticSearchUtils(host=host, index=index, split_index=True)

    def simplify(self, doc, title):
        """ """
        try:
            chat_list = doc['response']['continuationContents']['liveChatContinuation']['actions']
        except Exception as e:
            print('error at simplify', e)
            return []

        result = []
        for act_item in chat_list:
            if 'replayChatItemAction' not in act_item:
                return []

            for act in act_item['replayChatItemAction']['actions']:
                try:
                    chat_text = act['addChatItemAction']['item']['liveChatTextMessageRenderer']
                except Exception as e:
                    continue

                item = {
                    '_id': unquote(chat_text['id']),
                    'title': title,
                    'video_offset': int(act_item['replayChatItemAction']['videoOffsetTimeMsec']),
                    'time_stamp': chat_text['timestampText']['simpleText'],
                    'author': chat_text['authorName']['simpleText'],
                    'text': '\n'.join([v['text'].strip() for v in chat_text['message']['runs'] if 'text' in v]),
                    'curl_date': datetime.now(self.timezone).isoformat(),
                }

                try:
                    times_temp = int(chat_text['timestampUsec'][0:-3]) / 1000.0

                    dt = datetime.fromtimestamp(times_temp)
                    item['date'] = dt.astimezone(self.timezone).isoformat()
                except Exception as e:
                    print('error at parse date', [chat_text['timestampUsec'], e])

                result.append(item)

        return result

    def save_live_chat(self, chat, title, filename):
        """ """
        try:
            doc_list = self.simplify(doc=chat, title=title)

            for doc in doc_list:
                self.elastic.save_document(document=doc)

            self.elastic.flush()
        except Exception as e:
            print('error at save live chat', e)

        try:
            with open(filename, 'w') as fp:
                data = json.dumps(chat, ensure_ascii=False, indent=2)
                fp.write(data + '\n')
        except Exception as e:
            print('error at save live chat file', e)

        return

    def get_title(self):
        """ """
        try:
            ele = self.driver.find_element_by_css_selector('h1.title yt-formatted-string')
            if ele:
                return ele.text.replace('/', '-').replace('\n', '').strip()
        except Exception as e:
            print('get title error', e)

        return 'unknown'

    def get_live_chat(self, url_list):
        """ """
        i = 0
        pbar = tqdm(url_list)
        for url in pbar:
            pbar.set_description(str(i))

            if url in self.url_buf:
                continue

            self.url_buf[url] = 1

            f_name = '{:04d}'.format(i)

            url_info = self.parse_url(url)
            if 'playerOffsetMs' in url_info:
                f_name = url_info['playerOffsetMs']

            title = self.get_title()
            filename = '{}/{}/{}.json'.format(self.data_path, title, f_name)

            dir_path = dirname(filename)
            if isdir(dir_path) is False:
                makedirs(dir_path)

            if isfile(filename) is True:
                i += 1
                continue

            try:
                resp = requests.get(url, headers=self.headers)
                chat = resp.json()

                self.save_live_chat(chat=chat, title=title, filename=filename)
            except Exception as e:
                print('get live chat error', e)

            i += 1
            sleep(5)

        return

    def trace_networks(self):
        """ """
        self.make_path(self.data_path)

        url_list = []
        for ent in self.proxy.har['log']['entries']:
            url = ent['request']['url']
            if url.find('/get_live_chat') < 0:
                continue

            if url in self.url_buf:
                continue

            url_list.append(url)

        try:
            self.get_live_chat(url_list=url_list)
        except Exception as e:
            print('error trace networks', e)

        return

    def batch(self):
        """ """
        self.args = self.init_arguments()

        self.open_driver()

        self.home_path = 'data/youtube-live-chat/태산군주TV-리니지 생방송 다시보기 REC🔴'
        start_url = 'https://www.youtube.com/playlist?list=PLWeqEDf8g_W_Yh2iqHGA8tYiGZcESvQ-s'

        self.driver.get(start_url)
        self.driver.implicitly_wait(60)

        for i in range(100000):
            self.trace_networks()
            sleep(60 * 1)

        self.close_driver()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse
        from uuid import uuid1

        parser = argparse.ArgumentParser()

        # parser.add_argument('--user_data', default='cache/youtube/{}'.format(uuid1()), help='')
        parser.add_argument('--user_data', default=None, help='')
        parser.add_argument('--use_head', action='store_false', default=True, help='')

        parser.add_argument('--proxy_server', default='module/browsermob-proxy/bin/browsermob-proxy', help='')

        return parser.parse_args()


if __name__ == '__main__':
    utils = YoutubeLiveChatCrawler()

    utils.batch()
