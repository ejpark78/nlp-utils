#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os import makedirs
from os.path import isdir, isfile
from time import sleep
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup

from module.utils.logger import Logger
from glob import glob

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class TedCrawler(object):
    """ """

    def __init__(self):
        """생성자"""
        super().__init__()

        self.filename = {
            'url_list': 'data/ted/url-list.json',
            'talk_list': 'data/ted/talk-list.json',
        }

        self.env = self.init_arguments()

        self.logger = Logger()

        self.session = requests.Session()
        self.session.verify = False

        self.page_url = 'https://www.ted.com/talks?page={page}'
        self.language_url = 'https://www.ted.com/talks/{talk_id}/transcript.json?language={languageCode}'

    def get_html(self, url):
        """ """
        try:
            return self.session.get(url=url, verify=False, timeout=120)
        except Exception as e:
            self.logger.error({
                'method': 'get_html',
                'url': url,
                'e': str(e),
            })

        return None

    def get_language(self, talk_id, item):
        """ """
        path = 'data/ted/{}'.format(talk_id)

        item.update({'talk_id': talk_id})

        filename = '{}/{}.json'.format(path, item['languageCode'])
        if isfile(filename) is True:
            self.logger.log({
                'method': 'skip: language exists',
                'filename': filename,
            })
            return False

        url = self.language_url.format(**item)

        resp = self.get_html(url=url)
        if resp is None:
            sleep(self.env.sleep)
            return False

        try:
            with open(filename, 'w') as fp:
                fp.write(json.dumps(resp.json(), ensure_ascii=False, indent=4))

            self.logger.log({
                'method': 'get_language',
                'url': url,
                'status_code': resp.status_code,
                'filename': filename,
            })
        except Exception as e:
            self.logger.error({
                'method': 'get_language',
                'url': url,
                'status_code': resp.status_code,
                'filename': filename,
                'e': str(e),
            })

        return True

    def get_talk(self, url):
        """ """
        resp = self.get_html(url=url)
        if resp is None:
            sleep(self.env.sleep)
            return

        soup = BeautifulSoup(resp.content, 'lxml')

        tags = soup.find_all('script', {'data-spec': 'q'})
        if len(tags) == 0:
            self.logger.error({
                'method': 'get_talk',
                'url': url,
                'status_code': resp.status_code,
            })

            return None

        talk = str(tags[0]).replace('<script data-spec="q">q("talkPage.init",', '').replace(')</script>', '')

        ted = json.loads(talk)['__INITIAL_DATA__']

        if ted is None:
            self.logger.error({
                'method': 'get_talk',
                'url': url,
                'status_code': resp.status_code,
                'ted': ted,
                'talk': talk,
                'contents': soup.contents,
            })
            return None

        ted.update(ted['talks'][0])

        result = {
            'url': ted['url'],
            'title': ted['title'],
            'event': ted['event'],
            'recorded_at': ted['recorded_at'],
            'description': ted['description'],
            'speaker_name': ted['speaker_name'],
            'tags': ted['tags'],
            'talk_id': ted['id'],
            'name': ted['name'],
            'slug': ted['slug'],
            'viewed_count': ted['viewed_count'],
            'language': ted['language'],
            'languages': ted['downloads']['languages'],
            'related_talks': ted['related_talks'],
        }

        path = 'data/ted/{}'.format(result['talk_id'])
        if isdir(path) is False:
            makedirs(path)

        filename = '{}/talk-info.json'.format(path)
        with open(filename, 'w') as fp:
            fp.write(json.dumps(result, ensure_ascii=False, indent=4))

        self.logger.log({
            'method': 'get_talk',
            'url': url,
            'status_code': resp.status_code,
            'filename': filename,
        })

        return result

    def parse_talk_list(self, url):
        """ """
        resp = self.get_html(url=url)
        if resp is None:
            sleep(self.env.sleep)
            return

        soup = BeautifulSoup(resp.content, 'lxml')

        result = [urljoin(url, x['href']) for x in soup.select('div.col a.ga-link') if x.has_attr('href')]

        return list(set(result))

    def get_max_page(self, url):
        """ """
        resp = self.get_html(url=url)
        if resp is None:
            sleep(self.env.sleep)
            return -1

        soup = BeautifulSoup(resp.content, 'lxml')

        page_list = soup.select('div.pagination a')

        return max([int(x.get_text()) for x in page_list if x.get_text().isdecimal()])

    def trace_language(self):
        """ """
        file_list = glob('data/ted/*/talk-info.json')
        for i, filename in enumerate(file_list):
            with open(filename, 'r') as fp:
                ted = json.load(fp=fp)

            self.logger.log({
                'method': 'trace_language',
                'i': i,
                'total': len(file_list),
                'filename': filename,
                'language size': len(ted['languages']),
            })

            for item in ted['languages']:
                is_sleep = self.get_language(item=item, talk_id=ted['talk_id'])

                if is_sleep is True:
                    sleep(self.env.sleep)

        return

    def trace_talks(self, url_list):
        """ """
        with open(self.filename['talk_list'], 'r') as fp:
            ted_list = json.load(fp=fp)

        if len(url_list) == 0:
            with open(self.filename['url_list'], 'r') as fp:
                url_list = json.load(fp=fp)

        for i, u in enumerate(url_list):
            self.logger.log({
                'method': 'trace_talks',
                'i': i,
                'size': len(url_list),
            })

            if u in ted_list:
                self.logger.log({
                    'message': 'skip talk',
                    'talk_url': u,
                })
                continue

            ted = self.get_talk(url=u + '/transcript')
            if ted is None:
                self.logger.error({
                    'message': 'empty ted',
                    'url': u,
                })
                continue

            ted_list[u] = ted['talk_id']

            sleep(self.env.sleep)

        with open(self.filename['talk_list'], 'w') as fp:
            fp.write(json.dumps(ted_list, ensure_ascii=False, indent=4))

        return

    def trace_list(self):
        """ """
        max_page = self.get_max_page(url='https://www.ted.com/talks')

        url_list = []
        for page in range(max_page, 0, -1):
            url = self.page_url.format(page=page)

            url_list += self.parse_talk_list(url=url)

            self.logger.log({
                'method': 'trace_list',
                'page': page,
                'url': url,
                'talk_list': len(url_list),
            })
            sleep(self.env.sleep)

            with open(self.filename['url_list'], 'w') as fp:
                fp.write(json.dumps(url_list, ensure_ascii=False, indent=4))

        self.trace_talks(url_list=url_list)

        return

    def talk_list(self):
        """ """
        talk_list = {}
        for f in glob('data/ted/*/talk-info.json'):
            print(f)

            with open(f, 'r') as fp:
                info = json.load(fp=fp)

            talk_list[info['url']] = info['talk_id']

        with open(self.filename['talk_list'], 'w') as fp:
            fp.write(json.dumps(talk_list, ensure_ascii=False, indent=4))

        return

    def batch(self):
        """"""
        if self.env.list is True:
            self.trace_list()

        if self.env.talks is True:
            self.trace_talks(url_list=[])

        if self.env.language is True:
            self.trace_language()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--list', action='store_true', default=False)
        parser.add_argument('--talks', action='store_true', default=False)
        parser.add_argument('--language', action='store_true', default=False)

        parser.add_argument('--sleep', default=5, type=int)

        return parser.parse_args()


if __name__ == '__main__':
    TedCrawler().batch()
