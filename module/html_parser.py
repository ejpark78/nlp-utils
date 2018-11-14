#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import re

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class HtmlParser(object):
    """HTML 파싱"""

    def __init__(self):
        """ 생성자 """

    def parse(self, html, parsing_info, soup=None):
        """ 상세 정보 HTML 을 파싱한다."""
        if html is not None:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, 'html5lib')

        if soup is None:
            return None

        # 테그 정리
        self.replace_tag(soup, ['script', 'javascript', 'style'])

        self.remove_comment(soup)
        self.remove_banner(soup=soup)
        self.remove_attribute(soup, ['onclick', 'role', 'style', 'data-log'])

        result = {}
        for item in parsing_info:
            tag_list = []
            self.trace_tag(soup=soup, tag_list=item['tag'], index=0, result=tag_list)

            value_list = []
            for tag in tag_list:
                if item['type'] == 'text':
                    value = tag.get_text().strip().replace('\n', '')
                    value = re.sub('\s+', ' ', value)
                elif item['type'] == 'html':
                    value = str(tag)
                    try:
                        value = str(tag.prettify())
                    except Exception as e:
                        logging.error('{}'.format(e))
                else:
                    if tag.has_attr(item['type']):
                        value = tag[item['type']]
                    else:
                        value = str(tag.prettify())

                # replace
                if 'replace' in item:
                    for pattern in item['replace']:
                        value = re.sub('\r?\n', ' ', value, flags=re.MULTILINE)
                        value = re.sub(pattern['from'], pattern['to'], value, flags=re.DOTALL)

                value_list.append(value)

            if len(value_list) == 1:
                value_list = value_list[0]

            result[item['key']] = value_list

        return result

    @staticmethod
    def replace_tag(html_tag, tag_list, replacement='', attribute=None):
        """ html 태그 중 특정 태그를 삭제한다. ex) script, caption, style, ... """
        if html_tag is None:
            return False

        for tag_name in tag_list:
            for tag in html_tag.find_all(tag_name, attrs=attribute):
                if replacement == '':
                    tag.extract()
                else:
                    tag.replace_with(replacement)

        return True

    def trace_tag(self, soup, tag_list, index, result):
        """ 전체 HTML 문서에서 원하는 값을 가진 태그를 찾는다."""
        # from bs4 import element

        if soup is None:
            return

        if len(tag_list) == index and soup is not None:
            result.append(soup)
            return

        tag_info = tag_list[index]
        if 'attribute' not in tag_info:
            tag_info['attribute'] = None

        trace_soup = soup.find_all(tag_info['name'], attrs=tag_info['attribute'])

        if trace_soup is not None:
            for tag in trace_soup:
                self.trace_tag(soup=tag, tag_list=tag_list, index=index + 1, result=result)

        return

    @staticmethod
    def remove_comment(soup):
        """ html 태그 중에서 주석 태그를 제거한다.

        :param soup: 웹페이지 본문
        :return: True/False
        """
        from bs4 import Comment

        for element in soup(text=lambda text: isinstance(text, Comment)):
            element.extract()

        return True

    @staticmethod
    def remove_banner(soup):
        """ 베너 삭제를 삭제한다. """
        tag_list = soup.findAll('div', {'id': 'suicidalPreventionBanner'})
        for tag in tag_list:
            tag.extract()

        return soup

    @staticmethod
    def remove_attribute(soup, attribute_list):
        """ 속성을 삭제한다. """

        for tag in soup.findAll(True):
            if len(tag.attrs) == 0:
                continue

            new_attribute = {}
            for name in tag.attrs:
                if name in attribute_list:
                    continue

                if 'javascript' in tag.attrs[name] or 'void' in tag.attrs[name] or '#' in tag.attrs[name]:
                    continue

                new_attribute[name] = tag.attrs[name]

            tag.attrs = new_attribute

        return soup

    @staticmethod
    def parse_url(url):
        """url 에서 쿼리문을 반환한다."""
        from urllib.parse import urlparse, parse_qs

        url_info = urlparse(url)
        result = parse_qs(url_info.query)
        for key in result:
            result[key] = result[key][0]

        base_url = '{}://{}{}'.format(url_info.scheme, url_info.netloc, url_info.path)

        return result, base_url, url_info
