#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from bs4 import BeautifulSoup


class FBGroup(object):

    def __init__(self):
        """ """
        self.default = {
            "site": "https://m.facebook.com",
            "index": "crawler-facebook-ko",
            "reply_index": "crawler-facebook-ko-reply",
            "meta": {
                "lang_code": "ko",
                "category": "친구"
            }
        }

    def group(self):
        """ """
        soup = BeautifulSoup(open('data/group-list.html', 'r'), 'lxml')

        result = []

        for div in soup.select('div.bp9cbjyn'):
            url_list = [{'page': x['href'].replace('https://www.facebook.com/', ''), 'name': x.get_text()} for x in
                        div.select('a') if x.has_attr('href')]

            doc = json.loads(json.dumps(self.default))

            doc['page'] = url_list[-1]['page'].rstrip('/')
            doc['meta']['name'] = url_list[-1]['name']

            result.append(doc)

        with open('config/facebook/group.json', 'w') as fp:
            doc = {'list': result}

            fp.write(json.dumps(doc, indent=2, ensure_ascii=False))

        return

    def friends(self):
        """ """
        soup = BeautifulSoup(open('data/friends-list.html', 'r'), 'lxml')

        result = []

        for tag in soup.select('a'):
            if tag.has_attr('href') is False:
                continue

            url = tag['href']
            if url.find('facebook') < 0:
                continue

            if url.find('friends_mutual') > 0:
                continue

            name = tag.get_text().strip()
            if name == '':
                continue

            if url.find('ejpark78') > 0:
                continue

            print(url, name)

            doc = json.loads(json.dumps(self.default))

            doc['page'] = url.replace('https://www.facebook.com/', '').rstrip('/')
            doc['meta']['name'] = name

            result.append(doc)

        with open('config/facebook/friends.json', 'w') as fp:
            doc = {'list': result}

            fp.write(json.dumps(doc, indent=2, ensure_ascii=False))

        return

    def likes(self):
        """ """
        soup = BeautifulSoup(open('data/like-list.html', 'r'), 'lxml')

        result = []

        for tag in soup.select('a'):
            if tag.has_attr('href') is False:
                continue

            url = tag['href']
            if url.find('facebook') < 0:
                continue

            if url.find('friends_mutual') > 0:
                continue

            name = tag.get_text().strip()
            if name == '':
                continue

            if url.find('ejpark78') > 0:
                continue

            print(url, name.split('\n\n\n'))

            doc = json.loads(json.dumps(self.default))

            doc['page'] = url.replace('https://www.facebook.com/', '').rstrip('/')
            doc['meta']['name'], doc['meta']['category'] = name.split('\n\n\n')

            result.append(doc)

        with open('config/facebook/likes.json', 'w') as fp:
            doc = {'list': result}

            fp.write(json.dumps(doc, indent=2, ensure_ascii=False))

        return


if __name__ == '__main__':
    """ """
    FBGroup().likes()

    pass
