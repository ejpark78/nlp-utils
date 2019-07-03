#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import re
from datetime import datetime
from urllib.parse import urljoin

import pytz
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

from module.logging_format import LogMessage as LogMsg

logger = logging.getLogger()


class HtmlParser(object):
    """HTML 파싱"""

    def __init__(self):
        """ 생성자 """
        self.timezone = pytz.timezone('Asia/Seoul')

    @staticmethod
    def merge_values(item):
        """key 에 . 이 들어있는 컬럼을 합친다."""
        # key 에 . 이 들어있는 컬럼 분리
        new_item = {}
        remove_list = []
        for col in item:
            if col.find('.') < 0:
                continue

            remove_list.append(col)

            # reply_list.text 를 l1, l2로 분리
            l1, l2 = col.split('.', maxsplit=1)

            if l1 not in new_item:
                new_item[l1] = []

            # single value 일때
            values = item[col]
            if isinstance(values, list) is False:
                values = [values]

            # merge
            for i in range(len(values)):
                if len(new_item[l1]) <= i:
                    new_item[l1].append({l2: values[i]})
                    continue

                new_item[l1][i][l2] = values[i]

        # 합쳐진 항목 삭제
        for col in remove_list:
            if col not in item:
                continue

            del item[col]

        # 추출된 값 머지
        item.update(new_item)

        return item

    @staticmethod
    def parse_html(html, parser_type):
        """html 문서를 파싱한다."""
        soup = None

        html = html.replace('\r', '\n')

        html = re.sub('</tr>', '</tr>\n', html, flags=re.IGNORECASE | re.MULTILINE)
        html = re.sub('</p>', '</p>\n', html, flags=re.IGNORECASE | re.MULTILINE)
        html = re.sub('<table', '\n<table', html, flags=re.IGNORECASE | re.MULTILINE)
        html = re.sub('</dl>', '</dl>\n', html, flags=re.IGNORECASE | re.MULTILINE)
        html = re.sub('<br', '\n<br', html, flags=re.IGNORECASE | re.MULTILINE)

        if parser_type == 'lxml':
            soup = BeautifulSoup(html, 'lxml')
        elif parser_type == 'html5lib':
            soup = BeautifulSoup(html, 'html5lib')

        return soup

    def parse(self, parsing_info, base_url, html=None, soup=None):
        """ 상세 정보 HTML 을 파싱한다."""
        if html is not None:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, 'html5lib')

        if soup is None:
            return None

        # 태그 정리
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
                # 이미 값이 있는 경우
                if item['key'] in result:
                    val = result[item['key']]
                    if isinstance(val, str) and len(val) > 0:
                        continue

                    continue

                # 태그 삭제
                if 'remove' in item:
                    for pattern in item['remove']:
                        target_list = []
                        self.trace_tag(soup=tag, tag_list=[pattern], index=0, result=target_list)

                        for target in target_list:
                            target.extract()

                # 값 추출
                if item['type'] == 'text':
                    value = tag.get_text().strip()
                    value = re.sub('[ ]+', ' ', value)
                elif item['type'] == 'html':
                    try:
                        value = str(tag)
                    except Exception as e:
                        msg = {
                            'level': 'ERROR',
                            'message': 'html 추출 에러',
                            'exception': str(e),
                        }
                        logger.error(msg=LogMsg(msg))
                        continue

                    try:
                        value = str(tag.prettify())
                    except Exception as e:
                        msg = {
                            'level': 'ERROR',
                            'message': 'html prettify 에러',
                            'exception': str(e),
                        }
                        logger.error(msg=LogMsg(msg))
                else:
                    if tag.has_attr(item['type']):
                        value = tag[item['type']]
                    else:
                        value = str(tag.prettify())

                    # url 일 경우: urljoin
                    if item['type'] == 'src' or item['type'] == 'href':
                        value = urljoin(base_url, value)

                # 태그 삭제
                if 'delete' in item and item['delete'] is True:
                    tag.extract()

                # 문자열 치환
                if 'replace' in item:
                    for pattern in item['replace']:
                        value = re.sub('\r?\n', ' ', value, flags=re.MULTILINE)
                        value = re.sub(pattern['from'], pattern['to'], value, flags=re.DOTALL)

                        value = value.strip()

                # 타입 변환
                if 'type_convert' in item:
                    if item['type_convert'] == 'date':
                        value = self.parse_date(value)

                        # 날짜 파싱이 안된 경우
                        if isinstance(value, datetime) is False:
                            continue

                value_list.append(value)

            # 타입 제약: 디폴트 목록형
            if 'value_type' in item:
                if item['value_type'] == 'single':
                    if len(value_list) > 0:
                        value_list = value_list[0]
                    else:
                        value_list = ''

                if item['value_type'] == 'merge':
                    value_list = '\n'.join(value_list)

                if item['value_type'] == 'unique':
                    value_list = list(set(value_list))

            # 값의 개수가 하나인 경우, 스칼라로 변경한다.
            if isinstance(value_list, list):
                if len(value_list) == 0:
                    continue

                if len(value_list) == 1:
                    if value_list[0] == '':
                        continue

                    result[item['key']] = value_list[0]
                    continue
            elif value_list == '':
                continue

            result[item['key']] = value_list

        return result

    def trace_tag(self, soup, tag_list, index, result):
        """ 전체 HTML 문서에서 원하는 값을 가진 태그를 찾는다."""
        if soup is None:
            return

        if len(tag_list) == index and soup is not None:
            result.append(soup)
            return

        tag_info = tag_list[index]
        if 'attribute' not in tag_info:
            tag_info['attribute'] = None

        if 'select' in tag_info:
            # css select 인 경우
            trace_soup = soup.select(tag_info['select'])
        else:
            # 기존 방식
            trace_soup = soup.find_all(tag_info['name'], attrs=tag_info['attribute'])

        if trace_soup is not None:
            for tag in trace_soup:
                self.trace_tag(soup=tag, tag_list=tag_list, index=index + 1, result=result)

        return

    def parse_date(self, str_date):
        """날짜를 변환한다."""
        try:
            if '오전' in str_date:
                str_date = str_date.replace('오전', '') + ' AM'

            if '오후' in str_date:
                str_date = str_date.replace('오후', '') + ' PM'

            date = datetime.now(self.timezone)

            # 상대 시간 계산
            if '일전' in str_date:
                offset = int(str_date.replace('일전', ''))
                date += relativedelta(days=-offset)
            elif '분전' in str_date:
                offset = int(str_date.replace('분전', ''))
                date += relativedelta(minutes=-offset)
            elif '시간전' in str_date:
                offset = int(str_date.replace('시간전', ''))
                date += relativedelta(hours=-offset)
            elif str_date != '':
                dt = parse_date(str_date)
                date = self.timezone.localize(dt)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'html 날짜 변환 에러',
                'date': str_date,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

            return str_date

        return date

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

    @staticmethod
    def remove_comment(soup):
        """ html 태그 중에서 주석 태그를 제거한다."""
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
        query = parse_qs(url_info.query)
        for key in query:
            query[key] = query[key][0]

        base_url = '{}://{}{}'.format(url_info.scheme, url_info.netloc, url_info.path)

        return query, base_url, url_info

    @staticmethod
    def get_meta_value(soup):
        """ 메타 정보를 추출한다. """
        result = {}
        for meta in soup.findAll('meta'):
            key = meta.get('name', None)
            if key is None:
                key = meta.get('property', None)

            content = meta.get('content', None)

            if key is None or content is None:
                continue

            if key in result:
                # 문자열일 경우 배열로 변환
                if isinstance(result[key], str) and result[key] != content:
                    result[key] = [result[key]]

                # 배열일 경우 삽입, 중복 확인
                if isinstance(result[key], list) and content not in result[key]:
                    result[key].append(content)
            else:
                result[key] = content

        return result

    @staticmethod
    def get_encoding_type(html_body):
        """ 메타 정보에서 인코딩 정보 반환한다."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_body, 'html5lib')

        if soup.meta is None:
            return soup, None

        encoding = soup.meta.get('charset', None)
        if encoding is None:
            encoding = soup.meta.get('content-type', None)

            if encoding is None:
                content = soup.meta.get('content', None)

                match = re.search('charset=(.*)', content)
                if match:
                    encoding = match.group(1)
                else:
                    return soup, None

        return soup, encoding

    @staticmethod
    def get_tag_text(tag):
        """텍스트 반환"""
        import bs4

        if tag is None:
            return ''

        if isinstance(tag, bs4.element.NavigableString) is True:
            return str(tag).strip()

        return tag.get_text().strip()

    def extract_image(self, soup, base_url, delete_caption=False):
        """기사 본문에서 이미지와 캡션 추출"""

        result = []
        for tag in soup.find_all('img'):
            next_element = tag.next_element

            # 광고일 경우 iframe 으로 text 가 널이다.
            limit = 10
            if next_element is not None:
                str_next_element = self.get_tag_text(next_element)

                try:
                    while str_next_element == '':
                        limit -= 1
                        if limit < 0:
                            break

                        if next_element.next_element is None:
                            break

                        next_element = next_element.next_element
                        str_next_element = self.get_tag_text(next_element)

                    if len(str_next_element) < 200 and str_next_element.find('\n') < 0:
                        caption = str_next_element
                        result.append({
                            'image': urljoin(base_url, tag['src']),
                            'caption': caption
                        })
                    else:
                        next_element = None
                        result.append({
                            'image': urljoin(base_url, tag['src']),
                            'caption': ''
                        })
                except Exception as e:
                    msg = {
                        'level': 'ERROR',
                        'message': 'html 이미지 추출 에러',
                        'exception': str(e),
                    }
                    logger.error(msg=LogMsg(msg))
            else:
                result.append({
                    'image': urljoin(base_url, tag['src']),
                    'caption': ''
                })

            # 캡션을 본문에서 삭제
            if delete_caption is True:
                try:
                    if next_element is not None:
                        next_element.replace_with('')

                    tag.replace_with('')
                except Exception as e:
                    msg = {
                        'level': 'ERROR',
                        'message': 'html 이미지 캡션 추출 에러',
                        'exception': str(e),
                    }
                    logger.error(msg=LogMsg(msg))

        return result

    @staticmethod
    def parse_json(resp, url_info):
        """json 본문을 파싱한다."""
        item = resp

        mapping_info = {}
        if 'mapping' in url_info:
            mapping_info = url_info['mapping']

        for k in mapping_info:
            if k[0] == '_':
                continue

            v = mapping_info[k]
            if v == '' and k in item:
                del item[k]
                continue

            if v == '/' and k in item:
                item.update(item[k])
                del item[k]
                continue

        for k in mapping_info:
            if k[0] == '_':
                continue

            v = mapping_info[k]
            if v.find('{') < 0:
                continue

            item[k] = v.format(**resp)

        return item
