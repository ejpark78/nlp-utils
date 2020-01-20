#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys
from datetime import datetime
from time import sleep
from urllib.parse import urljoin
from uuid import uuid4

import urllib3
from tqdm.autonotebook import tqdm

from module.naver.dictionary.utils import DictionaryUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MESSAGE = 25

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(format='%(message)s')

logger = logging.getLogger()

logger.setLevel(MESSAGE)
logger.handlers = [logging.StreamHandler(sys.stderr)]


class ExampleSearchCrawler(DictionaryUtils):
    """사전 예문 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

    @staticmethod
    def get_values(tag, css, value_type='text'):
        values = tag.select(css)
        if len(values) == 0:
            return ''

        if value_type == 'text':
            return values[0].get_text()
        elif values[0].has_attr('href'):
            return values[0]['href']

        return ''

    def extract_values(self, soup):
        result = []
        for li in soup.find_all('li', {'class': 'utb'}):
            item = {
                'user_id': self.get_values(tag=li, css='div.trans dl dd a.id'),
                'date': self.get_values(tag=li, css='div.trans dl dd span'),
                'theme': self.get_values(tag=li, css='div.exam p.cate span.theme'),
                'level': self.get_values(tag=li, css='div.exam p.cate span.level'),
                'sentence1': self.get_values(tag=li, css='div.exam div.sentence span'),
                'sentence2': self.get_values(tag=li, css='div.exam div.mar_top1 a'),
                'correct': self.get_values(tag=li, css='div.vote span.correct2 strong'),
                'wrong': self.get_values(tag=li, css='div.vote span.wrong strong'),
                'more_url': self.get_values(tag=li, value_type='href', css='div.trans dl dd a.more02'),
                'more_count': self.get_values(tag=li, css='div.trans dl dd a.more02 b')
            }

            result.append(item)

        return result

    @staticmethod
    def get_max_page(soup):
        result = 0
        for tag in soup.select('div.sp_paging a'):
            result = tag['href'].replace('javascript:goPage(', '').replace(')', '')
            result = int(result)

        return result

    def trace_examples(self, url_frame, url_info, meta, sleep_time, index):
        """ """
        url_info['page'] = 1

        max_page = 2

        p_bar = None
        while url_info['page'] < max_page + 1:
            url = url_frame.format(**url_info)

            soup = self.get_html(url=url)
            data_list = self.extract_values(soup=soup)

            count = self.get_max_page(soup=soup)
            if max_page < count:
                max_page = count

                p_bar = tqdm(initial=url_info['page'], total=max_page, dynamic_ncols=True)

            if p_bar is not None:
                desc = '{:,}/{:,} {:,} {:,}'.format(url_info['page'], max_page, count, len(data_list))
                p_bar.set_description(desc=desc)

                p_bar.update(1)

            url_info['page'] += 1

            # 저장
            for doc in data_list:
                doc.update(meta)

                doc['curl_date'] = datetime.now(self.timezone).isoformat()

                doc['_id'] = str(uuid4())
                if 'more_url' in doc and len(doc['more_url']) > 0 and doc['more_url'][0] == '/':
                    doc['more_url'] = urljoin(url, doc['more_url'])

                self.elastic.save_document(index=index, document=doc)

            self.elastic.flush()

            sleep(sleep_time)

        return

    def batch(self):
        """"""
        index = 'crawler-naver-dictionary-user-translation'
        self.open_db(index=index)

        url_frame = '{site}?pageNo={page}&query={query}&fieldType={field}&degreeType={degree}&{extra}'

        url_info = {
            'page': 1,
            'site': 'https://endic.naver.com/search_example.nhn',
            'extra': 'sLn=kr&sortType=2&m=example&tab=2&themeId=1&levelId=1',
        }

        degree_list = {
            '초급': 2,
            '중급': 3,
            '고급': 1,
        }

        field_list = {
            '일반': '0',
            '정치': '1',
            '경제/금융': '2',
            'IT/과학': '3',
            '스포츠': '4',
            '학문': '5',
            '법률': '6',
            '예술/연예': '7',
            '원서': '13',
        }

        # query_list = 'a about afraid all and annoy are arrest as at be become bring but by can catch come could couldn do doesn ever fall feel fetch find for from give go got have he her here him his how i i\'d i\'m in into is it just keep l leave let make may might must my never no none of on or out over see shall she should so take that the then there they this thought to under was we what which will with would you your'.split(' ')

        query_list = 'then there they this thought to under was we what which will with would you your'.split(' ')

        for q in tqdm(query_list):
            for degree in tqdm(degree_list, desc=q):
                p_bar = tqdm(field_list, desc=degree)
                for field in p_bar:
                    p_bar.set_description(desc='{} {} {}'.format(field, degree, q))

                    url_info['query'] = q
                    url_info['field'] = field_list[field]
                    url_info['degree'] = degree_list[degree]

                    meta = {
                        'level': degree,
                        'domain': field,
                    }

                    self.trace_examples(
                        meta=meta,
                        index=index,
                        url_info=url_info,
                        url_frame=url_frame,
                        sleep_time=10,
                    )

        return


if __name__ == '__main__':
    ExampleSearchCrawler().batch()
