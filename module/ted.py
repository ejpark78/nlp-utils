#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from glob import glob
from os import makedirs, unlink
from os.path import isdir, isfile
from time import sleep
from urllib.parse import urljoin

import pytz
import requests
import urllib3
from bs4 import BeautifulSoup
from tqdm import tqdm

from module.utils.elasticsearch_utils import ElasticSearchUtils
from module.utils.logger import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class TedCorpusUtils(object):
    """ """

    def __init__(self):
        """생성자"""
        super().__init__()

        self.timezone = pytz.timezone('Asia/Seoul')

        self.index = 'crawler-ted'

        self.elastic = None

    def save_talks(self, talks):
        """ """
        if self.elastic is None:
            return

        for doc in talks:
            doc['_id'] = '{}-{}'.format(doc['talk_id'], doc['time'])

            self.elastic.save_document(document=doc, index=self.index)

        self.elastic.flush()

        return

    @staticmethod
    def read_languages(talk_id):
        """ """
        filter_lang = {'ko', 'en', 'id', 'vi', 'ja', 'zh-tw', 'zh-cn'}

        result = {}
        lang_list = []
        for filename in tqdm(glob('{}/*.json'.format(talk_id))):
            if 'talk-info' in filename:
                continue

            lang = filename.split('/')[-1].replace('.json', '')
            if lang not in filter_lang:
                continue

            with open(filename, 'r') as fp:
                content = ''.join(fp.readlines())
                if content.strip() == '':
                    continue

                doc = json.loads(content)

            lang_list.append(lang)

            if 'paragraphs' not in doc:
                if 'error' in doc:
                    unlink(filename)
                    print('error', doc, 'delete', filename)

                continue

            for paragraphs in doc['paragraphs']:
                for item in paragraphs['cues']:

                    s_id = int(item['time'])
                    if s_id not in result:
                        result[s_id] = {}

                    result[s_id][lang] = item['text'].strip().replace('\n', ' ')
                    result[s_id]['time'] = s_id
                    result[s_id]['talk_id'] = talk_id.split('/')[-1]

        return result, lang_list

    def insert_talks(self):
        """ """
        self.elastic = ElasticSearchUtils(
            host='https://corpus.ncsoft.com:9200',
            index=self.index,
            http_auth='elastic:nlplab',
        )

        path = 'data/ted/*'
        for talk_id in tqdm(glob(path)):
            if isdir(talk_id) is False:
                continue

            sentences, lang_list = self.read_languages(talk_id=talk_id)
            if len(lang_list) < 2:
                continue

            merged = []

            # marge english text
            for s_id, doc in sorted(sentences.items(), key=lambda x: x[0]):
                if len(merged) == 0:
                    merged.append(doc)
                    continue

                prev = merged[-1]
                if 'en' in prev and len(prev['en']) > 0 and re.match(r'[a-z,:;\-]', prev['en'][-1]) is not None:
                    for lang in lang_list:
                        if lang in merged[-1] and lang in doc:
                            merged[-1][lang] += ' ' + doc[lang]
                            continue

                        if lang not in doc:
                            doc[lang] = ''

                        merged[-1][lang] = doc[lang]

                    continue

                merged.append(doc)

            self.save_talks(talks=merged)

        return


class TedCrawlerUtils(TedCorpusUtils):
    """ """

    def __init__(self):
        """생성자"""
        super().__init__()

        self.env = None

        self.logger = Logger()

        self.session = requests.Session()
        self.session.verify = False

        self.filename = {
            'url_list': 'data/ted/url-list.json',
            'talk_list': 'data/ted/talk-list.json',
        }

        self.page_url = 'https://www.ted.com/talks?page={page}'
        self.language_url = 'https://www.ted.com/talks/{talk_id}/transcript.json?language={languageCode}'

    def get_html(self, url):
        """ """
        try:
            return self.session.get(url=url, verify=False, timeout=120)
        except Exception as e:
            self.logger.error({
                'ERROR': 'get_html',
                'url': url,
                'e': str(e),
            })

        return None

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

    def get_language(self, talk_id, item):
        """ """
        path = 'data/ted/{}'.format(talk_id)

        item.update({'talk_id': talk_id})

        # 1차
        # filter_lang = {'ko', 'en', 'id', 'vi', 'ja', 'zh-tw', 'zh-cn'}
        # if item['languageCode'] not in filter_lang:
        #     return False

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
            content = resp.json()
            if 'error' in content:
                return False
        except Exception as e:
            self.logger.error({
                'ERROR': 'get_language',
                'url': url,
                'status_code': resp.status_code,
                'filename': filename,
                'resp': resp.text,
                'e': str(e),
            })
            return False

        with open(filename, 'w') as fp:
            fp.write(json.dumps(content, ensure_ascii=False, indent=4))

        self.logger.log({
            'method': 'get_language',
            'url': url,
            'status_code': resp.status_code,
            'filename': filename,
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
                'ERROR': 'get_talk',
                'url': url,
                'status_code': resp.status_code,
            })

            return None

        talk = str(tags[0]).replace('<script data-spec="q">q("talkPage.init",', '').replace(')</script>', '')

        ted = json.loads(talk)['__INITIAL_DATA__']

        if ted is None:
            self.logger.error({
                'ERROR': 'get_talk',
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

    def update_talk_list(self):
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


class TedCrawler(TedCrawlerUtils):
    """ """

    def __init__(self):
        """생성자"""
        super().__init__()

        self.env = self.init_arguments()

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
                url_list = list(set(url_list))

        for i, u in enumerate(url_list):
            self.logger.log({
                'method': 'trace_talks',
                'i': i,
                'size': len(url_list),
            })

            if u in ted_list:
                self.logger.log({
                    'message': 'skip exists talk',
                    'talk_url': u,
                })
                continue

            ted = self.get_talk(url=u + '/transcript')
            if ted is None:
                self.logger.error({
                    'ERROR': 'empty ted',
                    'url': u,
                })
                continue

            ted_list[u] = ted['talk_id']

            with open(self.filename['talk_list'], 'w') as fp:
                fp.write(json.dumps(ted_list, ensure_ascii=False, indent=4))

            sleep(self.env.sleep)

        return

    def trace_list(self):
        """ """
        max_page = self.get_max_page(url='https://www.ted.com/talks')

        with open(self.filename['url_list'], 'r') as fp:
            url_list = json.load(fp=fp)

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
                url_list = list(set(url_list))
                fp.write(json.dumps(url_list, ensure_ascii=False, indent=4))

        self.trace_talks(url_list=url_list)

        return

    def batch(self):
        """"""
        if self.env.update_talk_list is True:
            self.update_talk_list()

        if self.env.list is True:
            self.trace_list()

        if self.env.talks is True:
            self.trace_talks(url_list=[])

        if self.env.language is True:
            self.trace_language()

        if self.env.insert_talks is True:
            self.insert_talks()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--list', action='store_true', default=False)
        parser.add_argument('--talks', action='store_true', default=False)
        parser.add_argument('--language', action='store_true', default=False)

        parser.add_argument('--insert_talks', action='store_true', default=False)
        parser.add_argument('--update_talk_list', action='store_true', default=False)

        parser.add_argument('--sleep', default=15, type=int)

        return parser.parse_args()


if __name__ == '__main__':
    TedCrawler().batch()

# find data/ted -size -2k -empty
# find data/ted -size -2k -empty -delete
