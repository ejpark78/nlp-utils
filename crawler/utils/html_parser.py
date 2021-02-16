#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs, ParseResult
from dotty_dict import dotty

import bs4
import pytz
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

from crawler.utils.logger import Logger


class HtmlParser(object):
    """HTML 파싱"""

    def __init__(self):
        self.logger = Logger()

        self.timezone = pytz.timezone('Asia/Seoul')

    @staticmethod
    def merge_values(item: dict) -> dict:
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
    def parse_html(html: str, parser_type: str) -> BeautifulSoup:
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
        else:
            soup = BeautifulSoup(html, 'html5lib')

        return soup

    def parse(self, parsing_info: list, base_url: str, html: str = None, soup: BeautifulSoup = None,
              parser_version: str = None) -> dict or None:
        """ 상세 정보 HTML 을 파싱한다."""
        if html is not None:
            soup = BeautifulSoup(html, 'html5lib')

        if soup is None:
            return None

        # 태그 정리
        self.replace_tag(soup=soup, tag_list=['script', 'javascript', 'style'], replacement='')

        # self.remove_banner(soup=soup)
        self.remove_comment(soup=soup)
        self.remove_attribute(soup, attribute_list=['onclick', 'style', 'data-log'])

        result = {}
        if parser_version is not None:
            result['parser_version'] = parser_version

        for conf in parsing_info:
            tag_list = []
            self.trace_tag(soup=soup, tag_list=conf['value'], index=0, result=tag_list)

            value_list = self.get_value_list(conf=conf, result=result, tag_list=tag_list, base_url=base_url)
            if value_list is None:
                continue

            result[conf['key']] = value_list

        return result

    def get_value_list(self, conf: dict, result: dict, tag_list: list, base_url: str) -> list or None:
        value_list = []
        for tag in tag_list:
            # 이미 값이 있는 경우
            if conf['key'] in result:
                continue

            val = self.extract_value(tag=tag, conf=conf, base_url=base_url)
            if val is None:
                continue

            value_list.append(val)

        # 타입 제약: 디폴트 목록형
        if 'value_type' in conf:
            if conf['value_type'] == 'single':
                if len(value_list) > 0:
                    value_list = value_list[0].strip() if isinstance(value_list, str) else value_list[0]
                else:
                    value_list = ''

            if conf['value_type'] == 'merge':
                value_list = '\n'.join(value_list).strip()

            if conf['value_type'] == 'unique':
                value_list = list(set(value_list))

        # 값의 개수가 하나인 경우, 스칼라로 변경한다.
        if isinstance(value_list, list):
            if len(value_list) == 0:
                return None

            if len(value_list) == 1:
                if value_list[0] == '':
                    return None

                result[conf['key']] = value_list[0]
                return None
        elif value_list == '':
            return None

        return value_list

    def extract_value(self, tag: BeautifulSoup, conf: dict, base_url: str):
        # 태그 삭제
        if 'remove' in conf:
            for pattern in conf['remove']:
                target_list = []
                self.trace_tag(soup=tag, tag_list=[pattern], index=0, result=target_list)

                for target in target_list:
                    target.extract()

        # 값 추출
        if conf['type'] == 'text':
            value = tag.get_text().strip()
            value = re.sub('[ ]+', ' ', value).strip()
        elif conf['type'] == 'html':
            try:
                value = str(tag)
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'html 추출 에러',
                    'exception': str(e),
                })
                return None

            try:
                value = str(tag.prettify())
            except Exception as e:
                self.logger.error(msg={
                    'level': 'ERROR',
                    'message': 'html prettify 에러',
                    'exception': str(e),
                })
        else:
            if tag.has_attr(conf['type']):
                value = tag[conf['type']]
            else:
                value = str(tag.prettify())

            # url 일 경우: urljoin
            if conf['type'] == 'src' or conf['type'] == 'href':
                value = urljoin(base_url, value)

        # 태그 삭제
        if 'delete' in conf and conf['delete'] is True:
            tag.extract()

        # 문자열 치환
        if 'replace' in conf:
            for pattern in conf['replace']:
                value = re.sub('\r?\n', ' ', value, flags=re.MULTILINE)
                value = re.sub(pattern['from'], pattern['to'], value, flags=re.DOTALL)

                value = value.strip()

        # 타입 변환
        if 'type_convert' in conf and conf['type_convert'] == 'date':
            value = self.parse_date(value)

            # 날짜 파싱이 안된 경우
            if isinstance(value, datetime) is False:
                return None

        return value

    def trace_tag(self, soup: BeautifulSoup, tag_list: list, index: int, result: list) -> None:
        """ 전체 HTML 문서에서 원하는 값을 가진 태그를 찾는다."""
        if soup is None:
            return

        if len(tag_list) == index and soup is not None:
            result.append(soup)
            return

        tag_info = tag_list[index]
        if 'const' in tag_info:
            if tag_info['const'] == 'DATE_NOW':
                dt = datetime.now(tz=self.timezone).isoformat()
                result.append(BeautifulSoup(dt))

            return

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

    def parse_date(self, str_date: str) -> datetime or None:
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
            elif '주전' in str_date:
                offset = int(str_date.replace('주전', ''))
                date += relativedelta(weeks=-offset)
            elif '분전' in str_date:
                offset = int(str_date.replace('분전', ''))
                date += relativedelta(minutes=-offset)
            elif '시간전' in str_date:
                offset = int(str_date.replace('시간전', ''))
                date += relativedelta(hours=-offset)
            elif 'days ago' in str_date or 'day ago' in str_date:
                offset = int(str_date.replace('days ago', '').replace('day ago', ''))
                date += relativedelta(days=-offset)
            elif 'weeks ago' in str_date or 'week ago' in str_date:
                offset = int(str_date.replace('weeks ago', '').replace('week ago', ''))
                date += relativedelta(weeks=-offset)
            elif 'hours ago' in str_date or 'hour ago' in str_date:
                offset = int(str_date.replace('hours ago', '').replace('hour ago', ''))
                date += relativedelta(hours=-offset)
            elif 'minutes ago' in str_date or 'minute ago' in str_date:
                offset = int(str_date.replace('minutes ago', '').replace('minute ago', ''))
                date += relativedelta(minutes=-offset)
            elif str_date != '':
                date = parse_date(str_date)
        except Exception as e:
            self.logger.warning(msg={
                'level': 'WARNING',
                'message': 'html 날짜 변환 경고',
                'str_date': str_date,
                'exception': str(e),
            })

            return None

        try:
            date = self.timezone.localize(date)
        except Exception as e:
            if 'tzinfo is already set' in str(e):
                return date

            self.logger.warning(msg={
                'level': 'WARNING',
                'message': 'datetime localize 경고',
                'date': date,
                'str_date': str_date,
                'exception': str(e),
            })
            return None

        return date

    @staticmethod
    def replace_tag(soup: BeautifulSoup, tag_list: list, replacement: str = '', attribute: dict = None) -> bool:
        """ html 태그 중 특정 태그를 삭제한다. ex) script, caption, style, ... """
        if soup is None:
            return False

        for tag_name in tag_list:
            for tag in soup.find_all(tag_name, attrs=attribute):
                if replacement == '':
                    tag.extract()
                else:
                    tag.replace_with(replacement)

        return True

    @staticmethod
    def remove_comment(soup: BeautifulSoup) -> bool:
        """ html 태그 중에서 주석 태그를 제거한다."""
        for element in soup(text=lambda text: isinstance(text, bs4.Comment)):
            element.extract()

        return True

    @staticmethod
    def remove_banner(soup: BeautifulSoup) -> BeautifulSoup:
        """ 베너 삭제를 삭제한다. """
        tag_list = soup.findAll('div', {'id': 'suicidalPreventionBanner'})
        for tag in tag_list:
            tag.extract()

        return soup

    @staticmethod
    def remove_attribute(soup: BeautifulSoup, attribute_list: list) -> BeautifulSoup:
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
    def parse_url(url: str) -> (dict, str, ParseResult):
        """url 에서 쿼리문을 반환한다."""
        url_info = urlparse(url)
        query = parse_qs(url_info.query)
        for key in query:
            query[key] = query[key][0]

        base_url = '{}://{}{}'.format(url_info.scheme, url_info.netloc, url_info.path)

        return query, base_url, url_info

    @staticmethod
    def get_meta_value(soup: BeautifulSoup) -> dict:
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
    def get_encoding_type(html_body: str) -> (BeautifulSoup, str):
        """ 메타 정보에서 인코딩 정보 반환한다."""
        soup = BeautifulSoup(html_body, 'html5lib')

        for x in soup.select('meta[charset]'):
            if x.has_attr('charset') is False:
                continue

            return soup, x['charset']

        for x in soup.select('meta[content-type]'):
            if x.has_attr('content-type') is False:
                continue

            return soup, re.sub('^.+charset=', '', x['content-type'])

        return soup, None

    @staticmethod
    def get_tag_text(tag: BeautifulSoup) -> str:
        """텍스트 반환"""
        from bs4.element import NavigableString

        if tag is None:
            return ''

        if isinstance(tag, NavigableString) is True:
            return str(tag).strip()

        return tag.get_text().strip()

    def extract_image(self, soup: BeautifulSoup, base_url: str, delete_caption: bool = False) -> list:
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
                    self.logger.error(msg={
                        'level': 'ERROR',
                        'message': 'html 이미지 추출 에러',
                        'exception': str(e),
                    })
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
                    self.logger.error(msg={
                        'level': 'ERROR',
                        'message': 'html 이미지 캡션 추출 에러',
                        'exception': str(e),
                    })

        return result

    def parse_json(self, resp: dict, mapping_info: dict) -> dict:
        """json 본문을 파싱한다."""
        result = {
            'json': json.dumps(resp, ensure_ascii=False)
        }

        dot = dotty(resp)

        for k in mapping_info:
            v = mapping_info[k]

            if dot.get(v) is not None and isinstance(dot[v], str):
                result[k] = dot[v]
                continue

            if v.find('{') < 0:
                continue

            result[k] = v.format(**resp)

            if k != 'date' or isinstance(result[k], datetime):
                continue

            try:
                result[k] = parse_date(result[k])
            except Exception as e:
                self.logger.warning(msg={
                    'level': 'WARNING',
                    'message': 'date 변환 경고',
                    'date': result[k],
                    'exception': str(e),
                })

        return result
