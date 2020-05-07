#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from datetime import datetime
from time import sleep
from urllib.parse import urlencode
from urllib.parse import urljoin
from uuid import uuid4

import urllib3
from bs4 import BeautifulSoup

from module.dictionary_utils import DictionaryUtils
from module.utils.logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(format='%(message)s')

logger = logging.getLogger()
logger.setLevel(MESSAGE)


class ExampleSearchCrawler(DictionaryUtils):
    """사전 예문 수집기"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

    def extract_values(self, soup):
        """ """
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
        """ """
        result = 0
        for tag in soup.select('div.sp_paging a'):
            result = tag['href'].replace('javascript:goPage(', '').replace(')', '')
            result = int(result)

        return result

    def trace_examples(self, url, url_info, meta, sleep_time, index):
        """ """
        page = 1
        max_page = 10

        while page < max_page + 1:
            resp = self.get_html(url=url, resp_type=url_info['resp_type'])

            if url_info['resp_type'] == 'json':
                ex_list = resp['searchResultMap']['searchResultListMap']['EXAMPLE']['items']

                max_page = resp['pagerInfo']['totalPages']
            else:
                ex_list = self.extract_values(soup=resp)

                count = self.get_max_page(soup=resp)
                if max_page < count:
                    max_page = count

            msg = {
                'level': 'MESSAGE',
                'message': '예문 검색',
                'page': page,
                'index': index,
                'max_page': max_page,
                'size': len(ex_list),
            }
            logger.log(level=MESSAGE, msg=LogMsg(msg))

            page += 1

            # 저장
            for doc in ex_list:
                doc.update(meta)

                for i in range(1, 6):
                    key = 'expExample{}'.format(i)

                    if key not in doc or doc[key] is None:
                        continue

                    text = BeautifulSoup(doc[key], 'html5lib').get_text()
                    doc['expExample{}Text'.format(i)] = text

                doc['curl_date'] = datetime.now(self.timezone).isoformat()

                doc['_id'] = str(uuid4())
                if 'more_url' in doc and len(doc['more_url']) > 0 and doc['more_url'][0] == '/':
                    doc['more_url'] = urljoin(url, doc['more_url'])

                self.elastic.save_document(index=index, document=doc)

            self.elastic.flush()

            sleep(sleep_time)

        return

    @staticmethod
    def get_url_info():
        """ """
        return [
            {
                'resp_type': 'json',
                'lang': 'id',
                'query_lang': ['id', 'ko'],
                'url_info': {
                    'page': 'page',
                    'site': 'https://dict.naver.com/api3/idko/search',
                    'query': {
                        'range': 'example',
                        'page': 1,
                        'query': ''
                    },
                }
            },
            {
                'resp_type': 'json',
                'lang': 'ru',
                'query_lang': ['ru', 'ko'],
                'url_info': {
                    'page': 'page',
                    'site': 'https://dict.naver.com/api3/ruko/search',
                    'query': {
                        'range': 'example',
                        'page': 1,
                        'query': ''
                    },
                }
            },
            {
                'resp_type': 'json',
                'lang': 'th',
                'query_lang': ['th', 'ko'],
                'url_info': {
                    'page': 'page',
                    'site': 'https://dict.naver.com/api3/thko/search',
                    'query': {
                        'range': 'example',
                        'page': 1,
                        'query': ''
                    },
                }
            },
            {
                'resp_type': 'json',
                'lang': 'ja',
                'query_lang': ['ja', 'ko', 'en'],
                'url_info': {
                    'page': 'page',
                    'site': 'https://ja.dict.naver.com/api3/jako/search',
                    'query': {
                        'query': '',
                        'm': 'pc',
                        'range': 'example',
                        'page': 1,
                        'shouldSearchVlive': 'false',
                    },
                }
            },
            {
                'resp_type': 'json',
                'lang': 'vi',
                'query_lang': ['vi', 'ko', 'en'],
                'url_info': {
                    'page': 'page',
                    'site': 'https://dict.naver.com/api3/viko/search',
                    'query': {
                        'query': '',
                        'm': 'pc',
                        'range': 'example',
                        'page': 1,
                        'shouldSearchProverb': 'true',
                        'lang': 'ko',
                        'shouldSearchVlive': 'false'
                    },
                }
            },
            {
                'resp_type': 'json',
                'lang': 'zh',
                'query_lang': ['zh', 'ko', 'en'],
                'url_info': {
                    'page': 'page',
                    'site': 'https://zh.dict.naver.com/api3/zhko/search',
                    'query': {
                        'query': '',
                        'm': 'pc',
                        'range': 'example',
                        'page': 1,
                        'lang': 'ko',
                        'shouldSearchVlive': 'false',
                        'articleAnalyzer': 'true',
                        'haveTrans': 'true'
                    },
                },
                'params': {
                    'exampleLevel': {
                        '전체': '',
                        '초급': 'exist:1',
                        '중급': 'exist:2',
                        '고급': 'exist:3',
                    },
                }
            },
            {
                'resp_type': 'html',
                'lang': 'ko',
                'query_lang': ['ko', 'en'],
                'url_info': {
                    'page': 'pageNo',
                    'site': 'https://endic.naver.com/search_example.nhn',
                    'query': {
                        'sLn': 'kr',
                        'ifAjaxCall': 'true',
                        'searchType': 'example',
                        'txtType': 0,
                        'langType': 0,
                        'isTranslatedType': 1,
                        'timeType': '4:3:2:1',
                        'ui': 'full',
                        'fieldType': 0,
                        'degreeType': 0,
                        'pageNo': 1,
                        'query': '',
                    },
                },
                'params': {
                    'langType': {
                        '전체': 0,
                        '미국': 4,
                        '영국': 3,
                        '캐나다': 2,
                        '호주': 1,
                    },
                    'degreeType': {
                        '전체': 0,
                        '초급': 2,
                        '중급': 3,
                        '고급': 1,
                    },
                    'fieldType': {
                        '전체': '',
                        '일반': '0',
                        '정치': '1',
                        '경제/금융': '2',
                        'IT/과학': '3',
                        '스포츠': '4',
                        '학문': '5',
                        '법률': '6',
                        '예술/연예': '7',
                        '원서': '13',
                        '명언': '11',
                        '속담': '12',
                        '칸아카데미': '14',
                    }
                }
            }
        ]

    def trace_entry_list(self):
        """ """
        url_list = self.get_url_info()

        self.open_db(index=self.args.index)

        for url_info in url_list:
            lang = url_info['lang']
            if lang != self.args.lang:
                continue

            state_column = 'state_{}'.format(lang)

            index = '{}-{}'.format(self.args.index, lang)

            for q_lang in url_info['query_lang']:
                entry_list = self.read_entry_list(lang=q_lang, column=state_column)

                for item in entry_list:
                    query = url_info['url_info']['query']

                    query['query'] = item['entry']

                    msg = {
                        'level': 'MESSAGE',
                        'message': '단어 검색',
                        'lang': lang,
                        'index': index,
                        'q_lang': q_lang,
                        'entry': item['entry'],
                    }
                    logger.log(level=MESSAGE, msg=LogMsg(msg))

                    url = '{}?{}'.format(url_info['url_info']['site'], urlencode(query))

                    meta = {
                        'lang': lang,
                        'q_lang': q_lang,
                    }

                    self.trace_examples(
                        url=url,
                        meta=meta,
                        index=index,
                        url_info=url_info,
                        sleep_time=10,
                    )

                    self.set_as_done(doc=item, column=state_column)

        return

    def batch(self):
        """"""
        self.args = self.init_arguments()

        self.logger = self.get_logger()

        if 'remove_same_example' in self.args and self.args.remove_same_example is True:
            self.remove_same_example()
        elif 'reset_list' in self.args and self.args.reset_list is True:
            self.reset_list(column='state_{}'.format(self.args.lang))
        elif 'upload_entry_list' in self.args and self.args.upload_entry_list is True:
            self.upload_entry_list()
        else:
            self.trace_entry_list()

        return

    def init_arguments(self):
        """ 옵션 설정 """
        parser = super().init_arguments()

        parser.add_argument('--index', default='crawler-dictionary-example-naver', help='')
        parser.add_argument('--list_index', default='crawler-dictionary-example-naver-list', help='')

        parser.add_argument('--lang', default=None, help='')

        return parser.parse_args()


if __name__ == '__main__':
    ExampleSearchCrawler().batch()
