#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from module.utils.selenium_utils import SeleniumUtils


class FBParser(SeleniumUtils):
    """페이스북 파서"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

    def parse_post(self, url, html):
        """포스트 내용을 추출한다."""
        soup = BeautifulSoup(html, 'html5lib')

        tag_list = soup.find_all('article')

        result = []
        for tag in tag_list:
            post = dict()

            for k, v in tag.attrs.items():
                if k not in ['data-ft', 'data-store']:
                    continue

                attrs = json.loads(v)
                post.update(attrs)

            post['raw_html'] = str(tag)

            # 메세지 추출
            span_list = tag.find_all('span', {'data-sigil': 'more'})
            if len(span_list) > 0:
                post['content'] = '\n'.join([v.get_text(separator='\n') for v in span_list])
                post['html_content'] = '\n'.join([v.prettify() for v in span_list])
            else:
                post['content'] = '\n'.join([v.get_text(separator='\n') for v in tag.find_all('p')])

                story_body = tag.find_all('div', {'class': 'story_body_container'})
                post['html_content'] = '\n'.join([v.prettify() for v in story_body])

            post['content'] = post['content'].replace('\n… \n더 보기\n', '')

            a_list = tag.find_all('a', {'data-sigil': 'feed-ufi-trigger'})
            post['url'] = [urljoin(url, v['href']) for v in a_list if v.has_attr('href')]
            if len(post['url']) > 0:
                post['url'] = post['url'][0]
            else:
                del post['url']

            # string 타입으로 변환
            post = self.to_string(doc=post)

            result.append(post)

        return result

    @staticmethod
    def to_string(doc):
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
    def parse_reply_body(tag):
        """ """
        raw_html = tag.prettify()

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

        result = {
            'user_name': user_name,
            'reply_to': reply_to,
            'reply_id': tag['data-commentid'],
            'text': tag.get_text(separator='\n'),
            'raw_html': raw_html,
        }

        return result
