#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from time import sleep

import urllib3
from bs4 import BeautifulSoup

from module.movie_reviews.naver.base import NaverMovieBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class NaverMovieReviews(NaverMovieBase):

    def __init__(self, params):
        super().__init__(params=params)

    def save_movie_reviews(self, code, title, content, meta):
        soup = BeautifulSoup(content, 'html5lib')

        buf = set()
        count = 0
        for item in soup.select('div.score_result ul li'):
            p = item.select('div.score_reple p')[0]
            span = p.select('span')

            comment = span[-1].get_text('\n').strip() if span is not None and len(span) > 0 else ''

            if comment == '':
                comment = p.get_text('\n').strip()

            review = {
                'code': code,
                'title': title,
                'score': ','.join([x.get_text() for x in item.select('div.star_score em')]),
                'comment': comment,
                'is_viewer': ','.join([x.get_text() for x in p.select('span.ico_viewer')]),
                'author': item.select('div.score_reple dl dt em span')[0].get_text(),
                'date': item.select('div.score_reple dl dt em')[-1].get_text(),
                'sympathy': item.select('div.btn_area a._sympathyButton strong')[-1].get_text(),
                'not_sympathy': item.select('div.btn_area a._notSympathyButton strong')[-1].get_text(),
            }

            if review['comment'] == '':
                continue

            buf.add(review['comment'])
            buf.add(review['date'])

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '영화 리뷰 저장',
                'count': len(buf) / 2 if len(buf) > 0 else 0,
                'date': review['date'],
                'score': review['score'],
                'comment': review['comment'],
                **meta
            })

            try:
                self.db.cursor.execute(
                    self.db.template['reviews'],
                    (title, code, json.dumps(review, ensure_ascii=False),)
                )

                count += 1
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '영화 리뷰 저장 오류',
                    'error': str(e),
                    **meta
                })

        self.db.conn.commit()

        return {
            'list': ','.join(list(buf)),
            'count': count
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

            prev = ''
            count = 0
            for p in range(1, 1000):
                url = self.url['reviews'].format(code=code, page=p)

                contents = self.db.read_cache(
                    url=url,
                    meta={
                        'title': title,
                        'page': p,
                        'position': '{:,}/{:,}'.format(i, len(rows)),
                    }
                )
                review_info = self.save_movie_reviews(
                    title=title,
                    code=code,
                    content=contents['content'],
                    meta={
                        'title': title,
                        'url': url,
                        'page': p,
                        'position': '{:,}/{:,}'.format(i, len(rows)),
                    }
                )
                count += review_info['count']

                if review_info['list'] == '':
                    self.logger.log(msg={
                        'level': 'MESSAGE',
                        'message': '영화 리뷰 없음',
                    })
                    break
                elif prev == review_info['list']:
                    self.logger.log(msg={
                        'level': 'MESSAGE',
                        'message': '영화 리뷰 중복',
                        'review_list': review_info['list'].split(',')
                    })
                    break

                prev = review_info['list']

                if contents['is_cache'] is False:
                    sleep(self.params.sleep)

            self.db.update_review_count(code=code, count=count)

        return
