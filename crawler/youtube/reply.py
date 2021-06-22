#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import brotli
import json
from time import sleep

import requests
from bs4 import BeautifulSoup

from crawler.youtube.core import YoutubeCore


class YoutubeReply(YoutubeCore):

    def __init__(self, params: dict):
        super().__init__(params=params)

    def get_total_reply_count(self) : # -> int:
        self.selenium.scroll(count=self.params['reply_scroll'], meta={})

        contents = []
        total = -1
        result_dict = dict()
        result_dict['total'] = total
        for x in self.selenium.get_requests(resp_url_path='/comment_service_ajax'):
            if hasattr(x, 'data') is False or len(x.data) < 2:
                continue

            if 'itemSectionContinuation' not in x.data['response']['continuationContents']:
                continue

            resp_item = x.data['response']['continuationContents']['itemSectionContinuation']
            if 'header' not in resp_item.keys():
                continue

            if 'commentsCount' not in resp_item['header']['commentsHeaderRenderer']:
                if 'countText' in resp_item['header']['commentsHeaderRenderer']:
                    total_text = '0'
                else:
                    continue
            else:
                total_text = resp_item['header']['commentsHeaderRenderer']['commentsCount']['runs'][0]['text']
            if 'contents' not in resp_item:
                contents += []
            else:
                contents += resp_item['contents']
            # contents += resp_item['contents']

            # total_text = resp_item['header']['commentsHeaderRenderer']['commentsCount']['runs'][0]['text']
            if '천' in total_text or 'K' in total_text:
                total_text = total_text.replace('천', '').replace('K', '')

                total = float(total_text) * 1000
            elif '만' in total_text or 'M' in total_text:
                total_text = total_text.replace('만', '').replace('M', '')

                total = float(total_text) * 10000
            else:
                total = float(total_text)

            total = round(total, 0)

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '댓글수',
                'total': total
            })
            if result_dict['total'] == -1: # 댓글 사용 중지
                result_dict['total'] = int(total)

            # return result_dict #int(total)

        replies = [x['commentThreadRenderer']['comment']['commentRenderer'] for x in contents]
        result_dict['replies'] = replies

        # return -1
        return result_dict #if result_dict['total'] > -1 else -1

    def get_more_reply(self, v_id: str, title: str, meta: dict, total: int, reply_sum: int = 0, max_try: int = 500,
                       max_zero_count: int = 5) -> int: # max_zero_count: int = 10
        if max_try < 0 or max_zero_count < 0:
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '댓글 조회 종료',
                'max_try': max_try,
                'total': total,
                'reply_sum': reply_sum,
                'max_zero_count': max_zero_count,
            })
            return reply_sum

        self.selenium.reset_requests()

        if total > 10:
            scroll_count = self.params['max_scroll'] if total > 20 else 3
            self.selenium.scroll(count=scroll_count, meta=meta)

        contents = []
        for x in self.selenium.get_requests(resp_url_path='/comment_service_ajax'):
            if hasattr(x, 'data') is False or 'response' not in x.data:
                continue

            if 'continuationContents' not in x.data['response']:
                continue

            if 'itemSectionContinuation' not in x.data['response']['continuationContents']:
                continue

            resp_item = x.data['response']['continuationContents']['itemSectionContinuation']
            if 'contents' not in resp_item:
                continue

            contents += resp_item['contents']

        replies = [x['commentThreadRenderer']['comment']['commentRenderer'] for x in contents]
        for data in replies:
            self.db.save_reply(
                c_id=data['commentId'],
                video_id=v_id,
                video_title=title,
                data=data
            )
        reply_sum += len(replies)
        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '댓글 조회',
            'count': len(replies),
            'reply_sum': reply_sum,
            'max_try': max_try,
            'total': total,
        })

        if len(replies) == 0:
            max_zero_count -= 1
        else:
            max_zero_count = 5
            sleep(self.params['sleep'])

        return self.get_more_reply(
            v_id=v_id,
            title=title,
            meta=meta,
            total=total,
            max_try=max_try - 1,
            reply_sum=reply_sum,
            max_zero_count=max_zero_count,
        )

        # return reply_sum

    def get_reply_first(self, replies: list, v_id: str, title: str, total: int) -> int:
        for data in replies:
            self.db.save_reply(
                c_id=data['commentId'],
                video_id=v_id,
                video_title=title,
                data=data
            )
        reply_sum = len(replies)
        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '댓글 조회',
            'count': len(replies),
            'reply_sum': reply_sum,
            'total': total,
        })

        return reply_sum

    def batch(self) -> None:
        self.db.cursor.execute('''SELECT id, title FROM videos WHERE reply_count < 0''')

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            v_id = item[0]
            title = item[1]

            reply_count = self.db.get_reply_count(v_id)
            if reply_count > 0:
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': 'SKIP VIDEO',
                    'item': item,
                    'position': i,
                })
                continue

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '댓글 조회',
                'video id': v_id,
                'title': title,
                'position': i,
                'size': len(rows)
            })

            url = f'''https://www.youtube.com/watch?v={v_id}'''
            self.selenium.open(
                url=url,
                resp_url_path=None,
                wait_for_path=None
            )

            total_dict = self.get_total_reply_count()
            if total_dict['total'] == -1: # 댓글 사용 중지인 경우
                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': '댓글 사용 중지',
                    'video id': v_id,
                    'title': title,
                    'position': i,
                })
                continue
                # sleep(15)
                # self.selenium.open(
                #     url=url,
                #     resp_url_path=None,
                #     wait_for_path=None
                # )
                # total_dict = self.get_total_reply_count()

            self.db.update_total(v_id=v_id, total=total_dict['total'])

            if total_dict['total'] == 0:
                self.db.update_reply_count(v_id=v_id, count=0)
                sleep(self.params['sleep'])
                continue

            reply_count = self.get_reply_first(total_dict['replies'],
                                               v_id=v_id,
                                               title=title,
                                               total=total_dict['total'])

            reply_count = self.get_more_reply(
                v_id=v_id,
                title=title,
                meta={'title': title, 'position': i},
                total=total_dict['total'],
                reply_sum=reply_count
            )

            self.db.update_reply_count(v_id=v_id, count=reply_count)
            sleep(self.params['sleep'])
            sleep(10)  # 잠시 텀 가지기

        return
