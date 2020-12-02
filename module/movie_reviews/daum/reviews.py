#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from time import sleep
from urllib.parse import urlparse, parse_qs

import urllib3

from module.movie_reviews.daum.base import DaumMovieBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DaumMovieReviews(DaumMovieBase):

    def __init__(self, params):
        super().__init__(params=params)

    def save_movie_reviews(self, code, title, content, meta):
        self.logger.log(msg={
            'level': 'MESSAGE',
            'message': '영화 리뷰 저장',
            **meta
        })

        reviews = json.loads(content)

        for item in reviews:
            try:
                self.db.cursor.execute(
                    self.db.template['reviews'],
                    (title, code, json.dumps(item, ensure_ascii=False),)
                )
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '영화 리뷰 저장 오류',
                    'error': str(e),
                    'content': content,
                    **meta
                })

        self.db.conn.commit()

        return len(reviews)

    @staticmethod
    def parse_comments_info(url, post, comment_info):
        post_id = post.data['post']['id']

        q = parse_qs(urlparse(url).query)
        query = dict(zip(q.keys(), [x[0] for x in q.values()]))

        size = int(query['limit'])
        total = comment_info.data['count'] + size

        return {
            'size': size,
            'total': total,
            'post_id': post_id,
        }

    def batch(self):
        _ = self.db.cursor.execute('SELECT code, title FROM movie_code WHERE review_count < 0')

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            (code, title) = (item[0], item[1])

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '영화 정보',
                'code': code,
                'title': title,
                'position': '{:,}/{:,}'.format(i, len(rows)),
            })

            info_url = self.url['info'].format(code=code)
            resp = self.selenium.open(
                url=info_url,
                resp_url_path='/apis/',
                wait_for_path=r'/apis/v1/comments/on/\d+/flag'
            )

            if len(resp) == 0:
                continue

            info = {
                'post': resp[0],
                'comments': resp[1],
                'comments_info': resp[2],
            }

            self.db.save_cache(url=info['post'].url, content=info['post'].response.body)
            self.db.save_cache(url=info['comments'].url, content=info['comments'].response.body)

            count = self.save_movie_reviews(
                code=code,
                title=title,
                content=info['comments'].response.body,
                meta={
                    'title': item[1],
                    'url': info['comments'].url,
                    'position': '{:,}/{:,}'.format(i, len(rows)),
                }
            )

            comments_info = self.parse_comments_info(
                url=info['comments'].url,
                post=info['post'],
                comment_info=info['comments_info']
            )
            self.db.update_total(code=code, total=comments_info['total'])

            for offset in range(comments_info['size'], comments_info['total'], comments_info['size']):
                url = self.url['reviews'].format(post_id=comments_info['post_id'], offset=offset)

                if offset // 1000 > 0 and offset % 1000 == 0:
                    _ = self.selenium.open(
                        url=info_url,
                        resp_url_path='/apis/',
                        wait_for_path=r'/apis/v1/comments/on/\d+/flag'
                    )

                contents = self.db.read_cache(
                    url=url,
                    meta={
                        'title': item[1],
                        'url': info['comments'].url,
                        'position': '{:,}/{:,}'.format(i, len(rows)),
                    },
                    headers=self.selenium.headers
                )

                if 'Access token expired' in contents['content'].decode('utf-8'):
                    _ = self.selenium.open(
                        url=info_url,
                        resp_url_path='/apis/',
                        wait_for_path=r'/apis/v1/comments/on/\d+/flag'
                    )

                    contents = self.db.read_cache(
                        url=url,
                        meta={
                            'title': item[1],
                            'url': info['comments'].url,
                            'position': '{:,}/{:,}'.format(i, len(rows)),
                        },
                        headers=self.selenium.headers,
                        use_cache=False,
                    )

                count += self.save_movie_reviews(
                    code=code,
                    title=title,
                    content=contents['content'],
                    meta={
                        'title': item[1],
                        'url': url,
                        'offset': offset,
                        'position': '{:,}/{:,}'.format(i, len(rows)),
                        'comments_info': comments_info
                    }
                )

                if contents['is_cache'] is False:
                    sleep(self.params.sleep)

            self.db.update_review_count(code=code, count=count)

        return
