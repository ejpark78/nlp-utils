#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from glob import glob
from os.path import isfile
from time import sleep

from module.ted.base import TedBase


class TedLanguage(TedBase):

    def __init__(self, params):
        super().__init__(params=params)

    def get_language(self, talk_id, item):
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
            sleep(self.params.sleep)
            return False

        try:
            content = resp.json()
            if 'error' in content:
                return False
        except Exception as e:
            self.logger.error({
                'ERROR': 'get language',
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
            'method': 'get language',
            'url': url,
            'status_code': resp.status_code,
            'filename': filename,
        })

        return True

    def batch(self):
        file_list = glob('data/ted/*/talk-info.json')
        for i, filename in enumerate(file_list):
            with open(filename, 'r') as fp:
                ted = json.load(fp=fp)

            self.logger.log({
                'method': 'trace language',
                'i': i,
                'total': len(file_list),
                'filename': filename,
                'language size': len(ted['languages']),
            })

            for item in ted['languages']:
                is_sleep = self.get_language(item=item, talk_id=ted['talk_id'])

                if is_sleep is True:
                    sleep(self.params.sleep)

            sleep(self.params.sleep)

        return
