#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from time import sleep
from urllib.parse import urljoin
from seleniumwire import webdriver
from selenium.webdriver.support.ui import WebDriverWait

import pytz
import urllib3
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.rrule import rrule, WEEKLY, MO

from module.sqlite_utils import SqliteUtils
from module.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class SeleniumWireUtils(object):

    def __init__(self):
        super().__init__()

        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.driver = None
        self.login = False
        self.headless = True
        self.user_data_path = None
        self.executable_path = '/usr/bin/chromedriver'

        self.open_driver()

    def open_driver(self):
        if self.driver is not None:
            return

        options = webdriver.ChromeOptions()

        if self.headless is True:
            options.add_argument('headless')

        options.add_argument('window-size=1920x1080')
        options.add_argument('disable-gpu')
        options.add_argument('disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-dev-shm-usage')

        if self.user_data_path is not None:
            options.add_argument('user-data-dir={}'.format(self.user_data_path))

        prefs = {
            'disk-cache-size': 4096,
            'profile.managed_default_content_settings.images': 2,
            'profile.default_content_setting_values.notifications': 2,
            'profile.managed_default_content_settings.stylesheets': 2,
            'profile.managed_default_content_settings.plugins': 1,
            'profile.managed_default_content_settings.popups': 2,
            'profile.managed_default_content_settings.geolocation': 2,
            'profile.managed_default_content_settings.media_stream': 2,
        }

        if self.login is True:
            prefs = {}

        options.add_experimental_option('prefs', prefs)

        self.driver = webdriver.Chrome(executable_path=self.executable_path, chrome_options=options)

        return

    def close_driver(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

        return

    def get(self, url):
        self.driver.get(url=url)

        self.driver.implicitly_wait(15)
        WebDriverWait(self.driver, 5, 10)

        result = []
        for req in self.driver.requests:
            if req.response is None:
                continue

            if '/apis/' not in req.url:
                continue

            req.json = json.loads(req.response.body)
            req.auth_token = req.headers['Authorization']

            result.append(req)

        return result


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

        self.db = SqliteUtils(filename=self.params.filename)
        self.db.use_cache = self.params.use_cache

    def save_movie_code(self, url, content):
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
            print(len(buf), values[1:])

            try:
                self.db.cursor.execute(self.db.template['code'], values)
            except Exception as e:
                print(e)

        self.db.conn.commit()

        return ','.join(list(buf))

    def get_movie_code(self):
        timezone = pytz.timezone('Asia/Seoul')

        dt_list = sorted(list(
            rrule(
                freq=WEEKLY,
                byweekday=MO,
                dtstart=parse_date('2004-01-01').astimezone(timezone),
                until=parse_date('2020-10-27').astimezone(timezone)
            )), reverse=True)

        for dt in dt_list:
            url = self.url['code'].format(year=dt.year, month=dt.month, day=dt.day)

            content, is_cache = self.db.get_contents(url=url, meta={})
            _ = self.save_movie_code(url=url, content=content)

            if is_cache is False:
                sleep(self.sleep_time)

        return

    def get_movie_info(self):
        import requests

        selenium = SeleniumWireUtils()

        _ = self.db.cursor.execute('SELECT code, title FROM movie_code')

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '영화 정보',
                'code': item[0],
                'title': item[1],
                'position': i,
                'size': len(rows)
            })

            info_url = self.url['info'].format(code=item[0])
            resp = selenium.get(url=info_url)

            reviews_url = self.url['reviews'].format(post_id=resp[0].json['post']['id'], offset=10)

            resp = requests.get(url=reviews_url, headers=resp[0].headers, timeout=120, verify=False)

            break

        return

    def save_movie_reviews(self, code, title, content, meta):
        soup = BeautifulSoup(content, 'html5lib')

        buf = set()
        for item in soup.select('div.score_result ul li'):
            p = item.select('div.score_reple p')[0]
            span = p.select('span')

            comment = span[-1].get_text().strip() if span is not None and len(span) > 0 else ''

            if comment == '':
                comment = p.get_text().strip()

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
                'message': '영화 리뷰 조회',
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
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': '영화 리뷰 저장 오류',
                    'error': str(e),
                    **meta
                })

        self.db.conn.commit()

        return ','.join(list(buf))

    def get_movie_reviews(self):
        _ = self.db.cursor.execute('SELECT code, title FROM movie_code')

        rows = self.db.cursor.fetchall()

        for i, item in enumerate(rows):
            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '영화 정보',
                'code': item[0],
                'title': item[1],
                'position': i,
                'size': len(rows)
            })

            prev = ''
            for p in range(1, 1000):
                url = self.url['reviews'].format(code=item[0], page=p)

                content, is_cache = self.db.get_contents(url=url, meta={})
                review_list = self.save_movie_reviews(title=item[1], code=item[0], content=content, meta={})

                if is_cache is False:
                    sleep(self.sleep_time)

                if review_list == '':
                    self.logger.log(msg={
                        'level': 'MESSAGE',
                        'message': '영화 리뷰 없음',
                    })
                    break

                if review_list != '' and prev == review_list:
                    self.logger.log(msg={
                        'level': 'MESSAGE',
                        'message': '영화 리뷰 중복',
                        'review_list': review_list.split(',')
                    })
                    break

                prev = review_list

        return

    def batch(self):
        if self.params.movie_code is True:
            self.get_movie_code()

        if self.params.movie_info is True:
            self.get_movie_info()

        if self.params.movie_reviews is True:
            self.get_movie_reviews()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--use-cache', action='store_true', default=False, help='캐쉬 사용')

        parser.add_argument('--movie-code', action='store_true', default=False, help='영화 코드 크롤링')
        parser.add_argument('--movie-info', action='store_true', default=False, help='영화 정보 크롤링')
        parser.add_argument('--movie-reviews', action='store_true', default=False, help='리뷰 크롤링')

        parser.add_argument('--filename', default='daum_movie_reviews.db', help='파일명')

        return parser.parse_args()


if __name__ == '__main__':
    DaumMovieReviews().batch()
