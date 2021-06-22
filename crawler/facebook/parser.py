#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag


class FacebookParser(object):
    """페이스북 파서"""

    def __init__(self):
        super().__init__()

    def parse_post(self, url: str, html: str) -> list:
        """포스트 내용을 추출한다."""
        soup = BeautifulSoup(html, 'html5lib')

        result = []
        for article in soup.find_all('article'):
            doc = dict()

            for k, v in article.attrs.items():
                if k not in ['data-ft', 'data-store']:
                    continue

                doc.update(json.loads(v))

            if 'top_level_post_id' not in doc:
                continue

            # contents 추출
            span_list = article.find_all('span', {'data-sigil': 'more'})
            if len(span_list) > 0:
                doc['contents'] = '\n'.join([v.get_text(separator='\n') for v in span_list])
                doc['html_contents'] = '\n'.join([v.prettify() for v in span_list])
            else:
                doc['contents'] = '\n'.join([v.get_text(separator='\n') for v in article.find_all('p')])

                story_body = article.find_all('div', {'class': 'story_body_container'})
                doc['html_contents'] = '\n'.join([v.prettify() for v in story_body])

            doc['contents'] = doc['contents'].replace('\n… \n더 보기\n', '')

            # url 추출
            a_list = article.find_all('a', {'data-sigil': 'feed-ufi-trigger'})
            doc['url'] = [urljoin(url, v['href']) for v in a_list if v.has_attr('href')]
            if len(doc['url']) > 0:
                doc['url'] = doc['url'][0]
            else:
                del doc['url']

            result.append({
                'top_level_post_id': doc['top_level_post_id'],
                'raw': str(article),
                'url': doc['url'],
                'contents': doc['contents'],
                'json': json.dumps(doc, ensure_ascii=False),
            })

        return result

    @staticmethod
    def to_string(doc: dict) -> dict:
        """ 문서의 각 필드값을 string 타입으로 변환한다. """
        for k in doc:
            if isinstance(doc[k], str) is True:
                continue

            if isinstance(doc[k], dict) is True or isinstance(doc[k], list) is True:
                doc[k] = json.dumps(doc[k])
                continue

            doc[k] = str(doc[k])

        return doc

    @staticmethod
    def parse_reply_body(tag: Tag) -> dict:
        user_name = ''
        for v in tag.parent.find_all('a'):
            if v['href'].find('/profile') is False:
                continue

            user_name = v.get_text()
            break

        reply_to = ''
        for v in tag.find_all('a'):
            if v['href'].find('/profile') is False:
                continue

            reply_to = v.get_text()
            v.extract()
            break

        return {
            'user_name': user_name,
            'reply_to': reply_to,
            'reply_id': tag['data-commentid'],
            'contents': tag.get_text(separator='\n'),
        }
