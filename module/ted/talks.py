#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from os import makedirs
from os.path import isdir
from time import sleep

from bs4 import BeautifulSoup

from module.ted.base import TedBase


class TedTalks(TedBase):

    def __init__(self, params):
        super().__init__(params=params)

    def get_talk(self, url):
        resp = self.get_html(url=url)
        if resp is None:
            sleep(self.params.sleep)
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

    def batch(self):
        url_list = []

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

            sleep(self.params.sleep)

        return
