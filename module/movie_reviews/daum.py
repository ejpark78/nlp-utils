#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from time import sleep
from urllib.parse import urljoin
from urllib.parse import urlparse, parse_qs

import pytz
import urllib3
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.rrule import rrule, WEEKLY, MO

from module.movie_reviews.cache_utils import CacheUtils
from module.utils.logger import Logger
from module.utils.selenium_wire_utils import SeleniumWireUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class DaumMovieReviews(object):

    def __init__(self):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.params = self.init_arguments()

        self.sleep_time = 15

        self.url = {
            'code': 'https://movie.daum.net/boxoffice/weekly?startDate={year}{month:02d}{day:02d}',
            'info': 'https://movie.daum.net/moviedb/main?movieId={code}',
            'grade': 'https://movie.daum.net/moviedb/grade?movieId={code}',
            'post': 'https://comment.daum.net/apis/v1/ui/single/main/@{code}',
            'reviews': 'https://comment.daum.net/apis/v1/posts/{post_id}/comments?'
                       'parentId=0&offset={offset}&limit=10&sort=RECOMMEND&isInitial=false&hasNext=true',
        }

        self.db = CacheUtils(filename=self.params.filename)
        self.db.use_cache = self.params.use_cache

        self.selenium = SeleniumWireUtils()

    def save_movie_code(self, url, content, meta):
        soup = BeautifulSoup(content, 'html5lib')

        buf = set()
        for item in soup.select('ul.list_movie li div.info_tit a'):
            if item.get_text() == '':
                continue

            if item['href'].find('movieId') < 0:
                continue

            values = (
                urljoin(url, item['href']),
                re.sub(r'^.+movieId=(\d+).*$', r'\g<1>', item['href']),
                item.contents[-1],
            )

            buf.add(values[1])

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '영화 코드 저장',
                'code': values[1],
                'title': values[2],
                **meta
            })

            try:
                self.db.cursor.execute(self.db.template['code'], values)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '영화 코드 저장 오류',
                    'code': values[1],
                    'title': values[2],
                    'error': str(e),
                    **meta
                })

        self.db.conn.commit()

        return ','.join(list(buf))

    def get_movie_code(self):
        timezone = pytz.timezone('Asia/Seoul')

        dt_list = sorted(list(
            rrule(
                freq=WEEKLY,
                byweekday=MO,
                dtstart=parse_date('2004-01-01').astimezone(self.timezone),
                until=parse_date('2020-10-27').astimezone(timezone)
            )), reverse=True)

        for dt in dt_list:
            url = self.url['code'].format(year=dt.year, month=dt.month, day=dt.day)

            contents = self.db.read_cache(url=url, meta={})
            _ = self.save_movie_code(url=url, content=contents['content'], meta={})

            if contents['is_cache'] is False:
                sleep(self.sleep_time)

        return

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

    def get_movie_reviews(self):
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
                    sleep(self.sleep_time)

            self.db.update_review_count(code=code, count=count)

        return

    def export(self):
        import pandas as pd

        db = CacheUtils(filename=self.params.filename)

        column = 'no,title,code,review'
        db.cursor.execute('SELECT {} FROM movie_reviews'.format(column))

        rows = db.cursor.fetchall()

        keys = 'id,postId,rating,content,childCount,likeCount,dislikeCount,recommendCount'.split(',')

        data = []
        for i, item in enumerate(rows):
            r = dict(zip(column.split(','), item))

            review = json.loads(r['review'])
            del r['review']

            r['username'] = review['userId']
            if 'displayName' in review['user']:
                r['username'] = review['user']['displayName']

            r['date'] = review['createdAt']

            for k in keys:
                if k not in review:
                    continue

                r[k] = review[k]
                if isinstance(review[k], str):
                    r[k] = str(review[k]).strip()

            data.append(r)

        df = pd.DataFrame(data)

        # xlsx
        writer = pd.ExcelWriter(
            '{}.reviews.xlsx'.format(self.params.filename),
            engine='xlsxwriter'
        )

        df.to_excel(writer, index=False, sheet_name='review')

        writer.save()

        # json
        df.to_json(
            '{}.reviews.json.bz2'.format(self.params.filename),
            force_ascii=False,
            compression='bz2',
            orient='records',
            lines=True,
        )

        return

    def batch(self):
        if self.params.movie_code is True:
            self.get_movie_code()

        if self.params.movie_reviews is True:
            self.get_movie_reviews()

        if self.params.export is True:
            self.export()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--movie-code', action='store_true', default=False, help='영화 코드 크롤링')
        parser.add_argument('--movie-info', action='store_true', default=False, help='영화 정보 크롤링')
        parser.add_argument('--movie-reviews', action='store_true', default=False, help='리뷰 크롤링')

        parser.add_argument('--export', action='store_true', default=False, help='내보내기')

        parser.add_argument('--filename', default='data/movie_reviews/daum.db', help='파일명')

        return parser.parse_args()


if __name__ == '__main__':
    DaumMovieReviews().batch()
