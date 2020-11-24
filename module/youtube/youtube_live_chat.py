#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from datetime import datetime
from os import makedirs
from os.path import isdir, dirname
from time import sleep
from urllib.parse import unquote

import requests

from utils import ElasticSearchUtils
from utils import SeleniumProxyUtils


class YoutubeLiveChatCrawler(SeleniumProxyUtils):
    """유튜브 라이브 채팅 크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.home_path = 'data/youtube-live-chat'
        self.data_path = self.home_path

        host = 'https://corpus.ncsoft.com:9200'
        index = 'crawler-youtube-live-chat'

        self.elastic = ElasticSearchUtils(
            host=host,
            index=index,
            split_index=True
        )

    def simplify(self, doc):
        try:
            chat_list = doc['response']['continuationContents']['liveChatContinuation']['actions']
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'simplify actions 추출 에러',
                'exception': str(e),
            })

            return []

        result = []
        for act_item in chat_list:
            if 'replayChatItemAction' not in act_item:
                return []

            for act in act_item['replayChatItemAction']['actions']:
                try:
                    chat_item = act['addChatItemAction']['item']

                    if 'liveChatTextMessageRenderer' not in chat_item:
                        continue

                    chat_text = chat_item['liveChatTextMessageRenderer']
                except Exception as e:
                    self.logger.error(msg={
                        'level': 'ERROR',
                        'message': 'simplify chat text 추출 에러',
                        'exception': str(e),
                        'act': act,
                    })
                    continue

                item = {
                    '_id': unquote(chat_text['id']),
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
                    self.logger.error(msg={
                        'level': 'ERROR',
                        'message': 'parse date 에러',
                        'chat_text': chat_text['timestampUsec'],
                        'exception': str(e),
                    })

                result.append(item)

        return result

    def save_live_chat(self, doc, meta):
        doc_list = self.simplify(doc=doc)

        try:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'live chat 저장',
                'length': len(doc),
                'meta': meta,
                'text': [doc['text'] for doc in doc_list],
            })
        except Exception as e:
            self.logger.error(e)

        try:
            for doc in doc_list:
                doc.update(meta)

                self.elastic.save_document(document=doc)

            self.elastic.flush()
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'save live chat 에러',
                'exception': str(e),
            })

        return

    def get_text(self, css):
        try:
            ele = self.driver.find_element_by_css_selector(css)
            if ele:
                return ele.text.replace('/', '-').replace('\n', '').strip()
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'get text 에러',
                'css': css,
                'exception': str(e),
            })

        return 'unknown'

    def get_meta(self, url):
        css = 'h1.title yt-formatted-string'
        title = self.get_text(css=css)

        css = 'div.style-scope ytd-video-owner-renderer div.style-scope ytd-channel-name'
        streamer = self.get_text(css=css)

        return {
            'url': url,
            'title': title,
            'streamer': streamer,
        }

    def get_live_chat(self, resp_list):
        i = 0
        for url in resp_list:
            if self.check_history(url=url) is True:
                continue

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'get live chat',
                'i': '{}/{}'.format(i, len(resp_list)),
                'url': url,
            })

            meta = self.get_meta(url=url)
            try:
                resp = requests.get(url, headers=self.headers, verify=False)
                doc = resp.json()

                self.save_live_chat(doc=doc, meta=meta)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'get live chat 에러',
                    'exception': str(e),
                })

            i += 1
            sleep(5)

        return

    def save_response(self, doc_list):
        i = 0
        for doc in doc_list:
            if self.check_history(url=doc['url']) is True:
                continue

            meta = self.get_meta(url=doc['url'])

            i += 1
            self.save_live_chat(doc=doc, meta=meta)

        return

    def dump_response(self, doc_list):
        from uuid import uuid4

        if len(doc_list) == 0:
            return

        filename = '{}/{}.json'.format(self.home_path, str(uuid4()))

        dir_path = dirname(filename)
        if isdir(dir_path) is False:
            makedirs(dir_path)

        with open(filename, 'w') as fp:
            for doc in doc_list:
                fp.write(json.dumps(doc, indent=4, ensure_ascii=False) + '\n')

        return

    def prepare(self):
        try:
            css = 'div.trigger paper-button#label'
            ele = self.driver.find_element_by_css_selector(css)
            if ele is not None:
                ele.click()

            xpath = '//*[@id="menu"]/a[2]'
            ele = self.driver.find_element_by_xpath(xpath)
            if ele is not None:
                ele.click()
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '실시간 채팅 다시보기 클릭 에러',
                'exception': str(e),
            })

        try:
            xpath = '//*[@id="ytp-id-21"]/div/div[2]/div[8]/div'

            ele = self.driver.find_element_by_xpath(xpath)
            if ele is not None:
                ele.click()
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '2배속 클릭 에러',
                'exception': str(e),
            })

        return

    def batch(self):
        self.args = self.init_arguments()

        self.open_driver()

        self.home_path = self.args.log_path

        start_url = 'https://www.youtube.com/playlist?list=PLmF_CDUVuBvjyepFjz-rDurq4Plnmh6zA'
        start_url = 'https://www.youtube.com/channel/UCymheuyZLem9B6XEAn0Iflg'
        start_url = 'https://www.youtube.com'
        start_url = 'https://www.youtube.com/watch?v=OmO1leAW-NU&list=PLb3XLk5iWovdtEntnFtiVpcnpA9POnlWg&index=13'

        self.driver.get(start_url)
        self.driver.implicitly_wait(60)
        sleep(10)
        # self.prepare()

        self.current_url = self.driver.current_url

        for i in range(100000):
            if self.args.trace_list is True:
                resp_list = self.trace_networks(path_list=['/playlist?', '/browse_ajax?'])
            else:
                resp_list = self.trace_networks(path_list=['/get_live_chat'])
                self.get_live_chat(resp_list=[x['url'] for x in resp_list])

            # doc_list = self.decode_response(content_list=resp_list)
            #
            # self.save_response(doc_list=doc_list)
            # self.dump_response(doc_list=doc_list)
            #
            # if self.current_url != self.driver.current_url:
            #     self.current_url = self.driver.current_url
            #
            #     self.close_driver()
            #     self.open_driver()
            #
            #     self.driver.get(self.current_url)
            #     self.driver.implicitly_wait(60)
            #     sleep(10)
            #
            #     # self.prepare()
            #
            # self.current_url = self.driver.current_url

            sleep(60 * 1)

        self.close_driver()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--trace_list', action='store_true', default=False, help='')
        parser.add_argument('--use_head', action='store_false', default=True, help='')

        parser.add_argument('--user_data', default='cache/selenium/youtube', help='')
        parser.add_argument('--log_path', default='data/youtube-live-chat', help='')

        parser.add_argument('--proxy_server', default='module/browsermob-proxy/bin/browsermob-proxy', help='')

        return parser.parse_args()


if __name__ == '__main__':
    utils = YoutubeLiveChatCrawler()

    utils.batch()
