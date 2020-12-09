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

import pytz
import requests

from module.youtube.base import YoutubeBase


class YoutubeLiveChat(YoutubeBase):

    def __init__(self, params):
        super().__init__(params=params)

        self.url_buf = {}

        self.timezone = pytz.timezone('Asia/Seoul')

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

    def check_history(self, url):
        if url in self.url_buf:
            return True

        self.url_buf[url] = 1

        return False

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
                resp = requests.get(url, headers=self.selenium.headers, verify=False)
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

    def batch(self):
        self.db.cursor.execute('SELECT id, title FROM videos LIMIT 1')

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            v_id = item[0]
            title = item[1]

            v_id = 's5kHF08Sqi4'

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '라이브 채팅 조회',
                'video id': v_id,
                'title': title,
                'position': i,
                'size': len(rows)
            })

            url = 'https://www.youtube.com/watch?v={v_id}'.format(v_id=v_id)
            self.selenium.open(
                url=url,
                resp_url_path=None,
                wait_for_path=None
            )

            resp_list = self.selenium.get_requests(resp_url_path='/get_live_chat')

            self.get_live_chat(resp_list=[x.url for x in resp_list])

            # doc_list = self.decode_response(content_list=resp_list)

            # self.save_response(doc_list=resp_list)
            # self.dump_response(doc_list=resp_list)

            pass

        return
