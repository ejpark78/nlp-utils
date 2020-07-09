#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os import makedirs
from os.path import isdir
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from module.utils.logger import Logger


class TedCrawler(object):
    """"""

    def __init__(self):
        """생성자"""
        super().__init__()

        self.logger = Logger()

        self.session = requests.Session()
        self.session.verify = False

        self.sleep = 5

    def get_language(self, ted):
        """ """
        path = 'data/ted/{}'.format(ted['talk_id'])
        if isdir(path) is False:
            makedirs(path)

        url_frame = 'https://www.ted.com/talks/{talk_id}/transcript.json?language={languageCode}'

        for item in ted['languages']:
            item.update({'talk_id': ted['talk_id']})

            url = url_frame.format(**item)

            resp = self.session.get(url=url, verify=False)

            filename = '{}/{}.json'.format(path, item['languageCode'])
            try:
                with open(filename, 'w') as fp:
                    fp.write(json.dumps(resp.json(), ensure_ascii=False, indent=4))
            except Exception as e:
                self.logger.error({
                    'method': 'get_language',
                    'url': url,
                    'status_code': resp.status_code,
                    'filename': filename,
                    'e': str(e),
                })

            self.logger.log({
                'method': 'get_language',
                'url': url,
                'status_code': resp.status_code,
                'filename': filename,
            })

            sleep(self.sleep)

        return

    def get_ted(self, url):
        """ """
        resp = self.session.get(url=url, verify=False)

        soup = BeautifulSoup(resp.content, 'lxml')

        tags = soup.find_all('script', {'data-spec': 'q'})
        if len(tags) == 0:
            self.logger.error({
                'method': 'get_ted',
                'url': url,
                'status_code': resp.status_code,
            })

            return None

        talk = str(tags[0]).replace('<script data-spec="q">q("talkPage.init",', '').replace(')</script>', '')

        ted = json.loads(talk)['__INITIAL_DATA__']

        if ted is None:
            self.logger.error({
                'method': 'get_ted',
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

        filename = 'data/ted/{}.json'.format(result['talk_id'])
        with open(filename, 'w') as fp:
            fp.write(json.dumps(result, ensure_ascii=False, indent=4))

        self.logger.log({
            'method': 'get_ted',
            'url': url,
            'status_code': resp.status_code,
            'filename': filename,
        })

        return result

    def get_page(self, url):
        """ """
        resp = self.session.get(url=url, verify=False)

        soup = BeautifulSoup(resp.content, 'lxml')

        result = [urljoin(url, x['href']) + '/transcript' for x in soup.select('div.col a.ga-link') if x.has_attr('href')]

        self.logger.log({
            'method': 'get_page',
            'url': url,
            'status_code': resp.status_code,
            'size': len(result),
        })

        return list(set(result))

    def batch(self):
        """"""
        page_url = 'https://www.ted.com/talks?page={page}'

        for page in range(1, 130):
            url = page_url.format(page=page)

            page_list = self.get_page(url=url)
            sleep(self.sleep)

            for u in page_list:
                ted = self.get_ted(url=u)
                sleep(self.sleep)

                if ted is None:
                    continue

                self.get_language(ted=ted)
                sleep(self.sleep)

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        return parser.parse_args()


if __name__ == '__main__':
    TedCrawler().batch()
