#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from datetime import datetime
from os.path import isfile
from time import sleep
from urllib.parse import unquote

import requests

from module.utils.elasticsearch_utils import ElasticSearchUtils
from module.utils.logging_format import LogMessage as LogMsg
from module.utils.proxy_utils import SeleniumProxyUtils


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

    def simplify(self, doc):
        """ """
        try:
            chat_list = doc['response']['continuationContents']['liveChatContinuation']['actions']
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'simplify actions 추출 에러',
                'exception': str(e),
            }
            self.logger.error(msg=LogMsg(msg))

            return []

        result = []
        for act_item in chat_list:
            if 'replayChatItemAction' not in act_item:
                return []

            for act in act_item['replayChatItemAction']['actions']:
                try:
                    chat_text = act['addChatItemAction']['item']['liveChatTextMessageRenderer']
                except Exception as e:
                    msg = {
                        'level': 'ERROR',
                        'message': 'simplify chat text 추출 에러',
                        'exception': str(e),
                    }

                    self.logger.error(msg=LogMsg(msg))
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
                    msg = {
                        'level': 'ERROR',
                        'message': 'parse date 에러',
                        'chat_text': chat_text['timestampUsec'],
                        'exception': str(e),
                    }

                    self.logger.error(msg=LogMsg(msg))

                result.append(item)

        return result

    def save_live_chat(self, doc, meta):
        """ """
        try:
            doc_list = self.simplify(doc=doc)

            for doc in doc_list:
                doc.update(meta)

                self.elastic.save_document(document=doc)

            self.elastic.flush()
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'save live chat 에러',
                'exception': str(e),
            }
            self.logger.error(msg=LogMsg(msg))

        return

    def get_text(self, css):
        """ """
        try:
            ele = self.driver.find_element_by_css_selector(css)
            if ele:
                return ele.text.replace('/', '-').replace('\n', '').strip()
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'get text 에러',
                'css': css,
                'exception': str(e),
            }

            self.logger.error(msg=LogMsg(msg))

        return 'unknown'

    def get_meta(self, url):
        """ """
        css = 'h1.title yt-formatted-string'
        title = self.get_text(css=css)

        css = 'div.style-scope ytd-video-owner-renderer div.style-scope ytd-channel-name'
        streamer = self.get_text(css=css)

        return {
            'url': url,
            'title': title,
            'streamer': streamer,
        }

    def check_history(self, url):
        """ """
        if url in self.url_buf:
            return True

        self.url_buf[url] = 1

        return False

    def get_live_chat(self, url_list):
        """ """
        i = 0
        for url in url_list:
            if self.check_history(url=url) is True:
                continue

            msg = {
                'level': 'MESSAGE',
                'message': 'get live chat',
                'i': '{}/{}'.format(i, len(url_list)),
                'url': url,
            }
            self.logger.log(level=self.MESSAGE, msg=LogMsg(msg))

            meta = self.get_meta(url=url)
            if isfile(meta['filename']) is True:
                i += 1
                continue

            try:
                resp = requests.get(url, headers=self.headers)
                doc = resp.json()

                self.save_live_chat(doc=doc, meta=meta)
            except Exception as e:
                msg = {
                    'level': 'ERROR',
                    'message': 'get live chat 에러',
                    'exception': str(e),
                }
                self.logger.error(msg=LogMsg(msg))

            i += 1
            sleep(5)

        return

    def is_valid_path(self, path_list, url):
        """ """
        if url in self.url_buf:
            return False

        for path in path_list:
            if url.find(path) < 0:
                continue

            return True

        return False

    def trace_networks(self, path_list):
        """ """
        self.make_path(self.data_path)

        url_list = []
        content_list = []
        for ent in self.proxy.har['log']['entries']:
            url = ent['request']['url']
            if self.is_valid_path(path_list=path_list, url=url) is False:
                continue

            url_list.append(url)

            try:
                content_list.append({
                    'url': url,
                    'content': ent['response']['content']
                })
            except Exception as e:
                msg = {
                    'level': 'ERROR',
                    'message': 'trace networks 에러',
                    'exception': str(e),
                }

                self.logger.error(msg=LogMsg(msg))

        if len(content_list) == 0:
            return

        doc_list = self.decode_response(content_list=content_list)
        self.save_response(doc_list=doc_list)

        self.dump_response(doc_list=doc_list)
        return

    def save_response(self, doc_list):
        """ """
        i = 0
        for doc in doc_list:
            if self.check_history(url=doc['url']) is True:
                continue

            meta = self.get_meta(url=doc['url'])

            i += 1
            self.save_live_chat(doc=doc, meta=meta)

        return

    def dump_response(self, doc_list):
        """ """
        from uuid import uuid4

        if len(doc_list) == 0:
            return

        filename = '{}/{}.json'.format(self.home_path, str(uuid4()))
        with open(filename, 'w') as fp:
            for doc in doc_list:
                fp.write(json.dumps(doc, indent=4, ensure_ascii=False) + '\n')

        return

    def decode_response(self, content_list):
        """ """
        import json
        import brotli
        from base64 import b64decode

        result = []
        for content in content_list:
            mime_type = content['content']['mimeType']
            if mime_type.find('json') < 0:
                continue

            try:
                text = content['content']['text']
                decoded_text = brotli.decompress(b64decode(text)).decode()

                doc = json.loads(decoded_text)
                if isinstance(doc, list):
                    for d in doc:
                        d['url'] = content['url']

                    result += doc
                else:
                    doc['url'] = content['url']
                    result.append(doc)
            except Exception as e:
                msg = {
                    'level': 'ERROR',
                    'message': 'decode response 에러',
                    'exception': str(e),
                }

                self.logger.error(msg=LogMsg(msg))

        return result

    def batch(self):
        """ """
        self.args = self.init_arguments()

        self.open_driver()

        self.home_path = 'data/youtube-live-chat'
        start_url = 'https://www.youtube.com'
        start_url = 'https://www.youtube.com/playlist?list=PLmF_CDUVuBvjyepFjz-rDurq4Plnmh6zA'
        start_url = 'https://www.youtube.com/channel/UCymheuyZLem9B6XEAn0Iflg'

        self.driver.get(start_url)
        self.driver.implicitly_wait(60)

        for i in range(100000):
            if self.args.trace_list is True:
                # self.page_down(10)
                self.trace_networks(path_list=['/playlist?', '/browse_ajax?'])
            else:
                self.trace_networks(path_list=['/get_live_chat'])

            sleep(60 * 1)

        self.close_driver()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--trace_list', action='store_true', default=False, help='')

        parser.add_argument('--user_data', default='cache/selenium/youtube', help='')
        parser.add_argument('--use_head', action='store_false', default=True, help='')

        parser.add_argument('--proxy_server', default='module/browsermob-proxy/bin/browsermob-proxy', help='')

        return parser.parse_args()


if __name__ == '__main__':
    utils = YoutubeLiveChatCrawler()

    utils.batch()
