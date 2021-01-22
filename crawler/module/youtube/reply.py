#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep

from module.youtube.base import YoutubeBase


class YoutubeReply(YoutubeBase):

    def __init__(self, params):
        super().__init__(params=params)

    def get_total_reply_count(self):
        self.selenium.scroll(count=3, meta={})

        for x in self.selenium.get_requests(resp_url_path='/comment_service_ajax'):
            if hasattr(x, 'data') is False or len(x.data) < 2:
                continue

            if 'itemSectionContinuation' not in x.data['response']['continuationContents']:
                continue

            resp_item = x.data['response']['continuationContents']['itemSectionContinuation']
            if 'header' not in resp_item.keys():
                continue

            if 'commentsCount' not in resp_item['header']['commentsHeaderRenderer']:
                continue

            total_text = resp_item['header']['commentsHeaderRenderer']['commentsCount']['simpleText']
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

            return total

        return -1

    def get_more_reply(self, v_id, title, meta, total, reply_sum=0, max_try=500, max_zero_count=10):
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
            scroll_count = self.params.max_scroll if total > 20 else 3
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

        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '댓글 조회',
            'count': len(replies),
            'reply_sum': reply_sum,
            'max_try': max_try,
            'total': total,
        })

        reply_sum += len(replies)

        if len(replies) == 0:
            max_zero_count -= 1
        else:
            max_zero_count = 10
            sleep(self.params.sleep)

        self.get_more_reply(
            v_id=v_id,
            title=title,
            meta=meta,
            total=total,
            max_try=max_try - 1,
            reply_sum=reply_sum,
            max_zero_count=max_zero_count,
        )

        return reply_sum

    def batch(self):
        self.db.cursor.execute('SELECT id, title FROM videos WHERE reply_count < 0')

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            v_id = item[0]
            title = item[1]

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '댓글 조회',
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

            total = self.get_total_reply_count()
            self.db.update_total(v_id=v_id, total=total)

            if total == 0:
                self.db.update_reply_count(v_id=v_id, count=0)
                sleep(self.params.sleep)
                continue

            reply_count = self.get_more_reply(
                v_id=v_id,
                title=title,
                meta={'title': title, 'position': i},
                total=total
            )

            self.db.update_reply_count(v_id=v_id, count=reply_count)
            sleep(self.params.sleep)

        return
