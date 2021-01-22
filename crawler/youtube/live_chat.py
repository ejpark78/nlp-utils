#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
from time import sleep
from urllib.parse import unquote

import pytz

from crawler.youtube.base import YoutubeBase


class YoutubeLiveChat(YoutubeBase):

    def __init__(self, params):
        super().__init__(params=params)

        self.url_buf = {}

        self.timezone = pytz.timezone('Asia/Seoul')

    def simplify(self, doc):
        try:
            chat_list = doc['continuationContents']['liveChatContinuation']['actions']
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
                    'username': chat_text['authorName']['simpleText'],
                    'text': '\n'.join([v['text'].strip() for v in chat_text['message']['runs'] if 'text' in v])
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

    def get_text(self, css):
        try:
            ele = self.selenium.driver.find_element_by_css_selector(css)
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

    def get_meta(self):
        css = 'h1.title yt-formatted-string'
        title = self.get_text(css=css)

        css = 'div.style-scope ytd-video-owner-renderer div.style-scope ytd-channel-name'
        streamer = self.get_text(css=css)

        return {
            'title': title,
            'streamer': streamer,
        }

    def check_history(self, url):
        if url in self.url_buf:
            return True

        self.url_buf[url] = 1

        return False

    def get_live_chat(self, resp_list, video_id):
        if len(resp_list) == 0:
            return

        for item in resp_list:
            if self.check_history(url=item.url) is True:
                continue

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': 'get live chat',
                'url': item.url,
            })

            doc_list = self.simplify(doc=item.data)
            for doc in doc_list:
                c_id = doc['_id']
                del doc['_id']

                self.db.save_live_chat(c_id=c_id, video_id=video_id, data=doc)

        return

    def batch(self):
        self.db.cursor.execute('SELECT id, title FROM videos LIMIT 1')

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            video_id = item[0]
            title = item[1]

            video_id = 'GSbMCHXFIc4'

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '라이브 채팅 조회',
                'video id': video_id,
                'title': title,
                'position': i,
                'size': len(rows)
            })

            url = 'https://www.youtube.com/watch?v={video_id}'.format(video_id=video_id)
            self.selenium.open(
                url=url,
                resp_url_path='/get_live_chat_replay',
                wait_for_path='/get_live_chat_replay'
            )

            for _ in range(10000000):
                resp_list = self.selenium.get_requests(resp_url_path='/get_live_chat_replay')
                self.get_live_chat(resp_list=resp_list, video_id=video_id)

                sleep(self.params.sleep)

        return
