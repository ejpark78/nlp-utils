#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import re
from datetime import datetime
from time import sleep
from urllib.parse import urljoin

import pytz
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from tqdm import tqdm

from module.elasticsearch_utils import ElasticSearchUtils
from module.selenium.selenium_utils import SeleniumUtils

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging.basicConfig(
    level=MESSAGE,
    format="[%(levelname)-s] %(message)s",
    handlers=[logging.StreamHandler()],
)


class SeleniumCrawler(SeleniumUtils):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        host = 'https://crawler:crawler2019@corpus.ncsoft.com:9200'
        index = 'crawler-bbs-naver'

        self.elastic = ElasticSearchUtils(host=host, index=index, split_index=True)

        self.timezone = pytz.timezone('Asia/Seoul')

    def scroll(self, count, start_article):
        """스크롤한다."""
        if start_article is not None:
            element = self.driver.find_element_by_class_name('u_cbox_btn_more')
            class_name = element.get_attribute('class')

            class_name = re.sub(
                r'\|FindMoreArticleList\|(\d+)\|(\d+)\|',
                r'|FindMoreArticleList|\g<1>|' + str(start_article['articleid']) + '|',
                class_name
            )

            self.driver.execute_script("arguments[0].setAttribute('class','" + class_name + "')", element)

        for _ in range(count):
            try:
                self.driver.find_element_by_class_name('u_cbox_btn_more').click()
            except Exception as e:
                print('scroll error: ', e)

            self.driver.implicitly_wait(10)

            sleep(5)

        return

    def save_list(self, page_list, cafe_name):
        """추출한 정보를 저장한다."""
        for doc in page_list:
            url = self.parse_url(url=doc['url'])

            if 'clubid' not in url and 'articleid' not in url:
                continue

            doc['_id'] = '{clubid}-{articleid}'.format(**url)

            doc['cafe_name'] = cafe_name
            doc['curl_date'] = datetime.now(self.timezone).isoformat()

            self.elastic.save_document(document=doc, delete=False)

        self.elastic.flush()

        return

    def save_contents(self, doc, flush=True):
        """추출한 정보를 저장한다."""
        url = self.parse_url(url=doc['url'])

        if 'clubid' not in url and 'articleid' not in url:
            return

        doc['_id'] = '{clubid}-{articleid}'.format(**url)

        doc['curl_date'] = datetime.now(self.timezone).isoformat()

        self.elastic.save_document(document=doc, delete=False)
        if flush is True:
            self.elastic.flush()

        return

    def delete_post(self):
        """태그 삭제"""
        script = 'document.querySelectorAll("li.board_box").forEach(function(ele) {ele.remove();})'

        try:
            self.driver.execute_script(script)
        except Exception as e:
            print('delete post error', e, flush=True)

        self.driver.implicitly_wait(10)

        return

    def get_page_list(self, url, html):
        """포스트 내용을 추출한다."""
        soup = BeautifulSoup(html, 'html5lib')

        tag_list = soup.find_all('li', {'class': 'board_box'})

        result = []
        for box in tag_list:
            post = dict()

            post['title'] = ''.join([v.get_text().strip() for v in box.find_all('strong', {'class': 'tit'})])
            post['nick'] = ''.join([v.get_text().strip() for v in box.select('div.user_area span.nick span.ellip')])

            post['view_count'] = ''.join([v.get_text().strip() for v in box.select('div.user_area span.no')])
            post['reply_count'] = ''.join([v.get_text().strip() for v in box.select('em.num')])

            for k in ['view_count', 'reply_count']:
                if post[k].find('만') > 0:
                    post[k] = eval(post[k].replace('만', '*10000'))
                    continue

                post[k] = int(post[k].replace(',', '').replace('+', '').replace('조회', '').strip())

            post['url'] = urljoin(url, [v['href'] for v in box.find_all('a') if v.has_attr('href')][0])

            try:
                dt = ''.join([v.get_text().strip() for v in box.select('div.user_area span.time')])
                if dt != '':
                    post['date'] = parse_date(dt).astimezone(self.timezone).isoformat()
            except Exception as e:
                print(e)

            query_info = self.parse_url(url=post['url'])
            for k in query_info:
                if k.find('id') < 0:
                    continue

                post[k] = int(query_info[k])

            result.append(post)

        return result

    def get_contents(self, item):
        """컨텐츠 하나를 조회한다."""
        self.open_driver()

        self.driver.get(item['url'])
        self.driver.implicitly_wait(3)

        html = self.driver.page_source

        soup = BeautifulSoup(html, 'html5lib')

        item['bbs_name'] = ''.join([v.get_text().strip() for v in soup.select('div.tit_menu a span.ellip')])

        dt = ''.join([v.get_text().strip() for v in soup.select('div.info > span.date.font_l')])
        dt = dt.replace('작성일', '').strip()

        if dt == '':
            tags = [v.get_text().strip() for v in soup.select('div.post_info > span.board_time > span')]
            if len(tags) > 0:
                dt = tags[0]

        if dt != '':
            try:
                item['date'] = parse_date(dt).astimezone(self.timezone).isoformat()
            except Exception as e:
                print({'date parse error', dt, e})

        item['image'] = []
        item['content'] = ''
        item['html_content'] = ''

        for content in soup.select('div#postContent'):
            item['image'] += [v['src'] for v in content.find_all('img') if v.has_attr('src')]

            item['content'] += content.get_text().strip()
            item['html_content'] += str(content)

        reply_list = []
        for li in soup.select('div#commentArea ul li'):
            if li.has_attr('class') is False:
                continue

            reply_item = {
                'class': ' '.join(li['class']),
                'text': ''.join([v.get_text().strip() for v in li.select('p.txt')]),
                'date': ''.join([v.get_text().strip() for v in li.select('span.date')]),
                'nick': ''.join([v.get_text().strip() for v in li.select('span.name.ellip')]),
                'image': ''.join([''.join(v['class']).split('|')[-1].split(')')[0] for v in
                                  li.select('div.image_wrap a.image_link')]),
                'reply_to': ''.join([v.get_text().strip() for v in li.select('a.u_cbox_target_name')]),
            }

            if reply_item['date'] != '':
                try:
                    reply_item['date'] = parse_date(reply_item['date']).astimezone(self.timezone).isoformat()
                except Exception as e:
                    print({'date parse error', reply_item['date'], e})
                    del reply_item['date']
            else:
                del reply_item['date']

            reply_list.append(reply_item)

        item['reply_list'] = reply_list

        return

    def rename_doc_id(self):
        """ """
        # query = {
        #     'query': {
        #         "wildcard": {
        #             "document_id": {
        #                 "value": "201912*",
        #                 "boost": 1.0,
        #                 "rewrite": "constant_score"
        #             }
        #         }
        #     }
        # }

        query = {
            'query': {
                'bool': {
                    'must_not': {
                        'exists': {
                            'field': 'replay_count'
                        }
                    }
                }
            }
        }

        # query = {
        #     'query': {
        #         "wildcard": {
        #             "view_count": {
        #                 "value": "*,*",
        #                 "boost": 1.0,
        #                 "rewrite": "constant_score"
        #             }
        #         }
        #     }
        # }

        # query = {}

        id_list = self.elastic.get_id_list(index=self.elastic.index, query_cond=query)
        id_list = list(id_list)

        size = 1000

        start = 0
        end = size

        while start < len(id_list):
            doc_list = []
            self.elastic.get_by_ids(id_list=id_list[start:end], index=self.elastic.index, source=None, result=doc_list)

            if start >= len(id_list):
                break

            start = end
            end += size

            if end > len(id_list):
                end = len(id_list)

            pbar = tqdm(doc_list, desc='{:,}~{:,}'.format(start, end))
            for doc in pbar:
                url = self.parse_url(url=doc['url'])
                # doc['_id'] = '{clubid}-{articleid}'.format(**url)

                # self.elastic.elastic.delete(self.elastic.index, '_doc', id=doc['document_id'])

                if 'replay_count' not in doc:
                    continue

                doc['reply_count'] = doc['replay_count'].replace('+', '')
                del doc['replay_count']

                self.save_contents(doc=doc, flush=False)

            self.elastic.flush()

        return

    def trace_contents(self, bbs_info):
        """모든 컨텐츠를 수집한다."""
        query = {
            'sort': [{
                'date': 'desc'
            }],
            'query': {
                'bool': {
                    'must': {
                        'match': {
                            'clubid': bbs_info['clubid']
                        }
                    },
                    'must_not': {
                        'exists': {
                            'field': 'html_content'
                        }
                    }
                }
            }
        }

        id_list = self.elastic.get_id_list(index=self.elastic.index, query_cond=query)
        id_list = list(id_list)

        size = 1000

        start = 0
        end = size

        while start < len(id_list):
            doc_list = []
            self.elastic.get_by_ids(id_list=id_list[start:end], index=self.elastic.index, source=None, result=doc_list)

            if start >= len(id_list):
                break

            start = end
            end += size

            if end > len(id_list):
                end = len(id_list)

            self.open_driver()

            pbar = tqdm(doc_list, desc='{} {:,}~{:,}'.format(bbs_info['name'], start, end))
            for doc in pbar:
                if 'html_content' in doc and doc['html_content'] == '':
                    continue

                url = self.parse_url(url=doc['url'])

                if 'clubid' not in url and 'articleid' not in url:
                    continue

                pbar.set_description(bbs_info['name'] + ' ' + str(url['articleid']))

                self.get_contents(item=doc)

                self.save_contents(doc=doc)
                sleep(5)

            self.close_driver()

        return

    def get_min_article_id(self, club_id):
        """ """
        query = {
            '_source': ['articleid', 'cafe_name', 'date'],
            'size': 1,
            'sort': [{
                'articleid': 'asc'
            }],
            'query': {
                'match': {
                    'clubid': club_id
                }
            }
        }

        search_result = self.elastic.elastic.search(
            index=self.elastic.index,
            body=query,
            size=1,
        )

        hits = search_result['hits']

        if hits['total']['value'] == 0:
            return None

        doc = [x['_source'] for x in hits['hits']][0]

        return doc

    def get_contents_list(self, bbs_info, continue_list=False, max_iter=2):
        """하나의 계정을 모두 읽어드린다."""
        self.open_driver()

        self.driver.get(bbs_info['url'])
        self.driver.implicitly_wait(10)

        start_article = None
        if continue_list is True:
            start_article = self.get_min_article_id(club_id=bbs_info['clubid'])

        pbar = tqdm(range(max_iter))
        for _ in pbar:
            self.scroll(count=2, start_article=start_article)
            self.driver.implicitly_wait(5)

            if start_article is not None:
                pbar.set_description(str(start_article['articleid']))

            start_article = None

            try:
                page_list = self.get_page_list(url=bbs_info['url'], html=self.driver.page_source)
            except Exception as e:
                print({'get page error', e})
                continue

            if page_list is None or len(page_list) == 0:
                break

            self.save_list(page_list=page_list, cafe_name=bbs_info['name'])

            if start_article is None and len(page_list) > 0 and 'articleid' in page_list[0]:
                pbar.set_description(str(page_list[0]['articleid']))

            # 태그 삭제
            self.delete_post()

        self.close_driver()

        return

    def batch(self):
        """"""
        self.args = self.init_arguments()

        bbs_list = self.read_config(filename=self.args.config)

        pbar = tqdm(bbs_list)
        for bbs in pbar:
            if self.args.clubid is not None and self.args.clubid != bbs['clubid']:
                continue

            bbs['url'] = bbs['url'].format(**bbs)

            if self.args.list:
                pbar.set_description(bbs['name'] + ' list')

                bbs['max_page'] = self.args.max_page
                if self.args.c is True:
                    bbs['max_page'] = 5000

                self.get_contents_list(bbs_info=bbs, max_iter=bbs['max_page'], continue_list=self.args.c)

            if self.args.contents:
                pbar.set_description(bbs['name'] + 'contents')

                self.trace_contents(bbs_info=bbs)

        if self.args.rename_doc_id:
            pbar.set_description('rename_id')

            self.rename_doc_id()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-config', default='./config/naver.bbs.list.json', help='')
        parser.add_argument('-user_data', default='./cache/selenium/naver-cafe', help='')

        parser.add_argument('-list', action='store_true', default=False, help='')
        parser.add_argument('-contents', action='store_true', default=False, help='')
        parser.add_argument('-rename_doc_id', action='store_true', default=False, help='')
        parser.add_argument('-c', action='store_true', default=False, help='')

        parser.add_argument('-use_head', action='store_false', default=True, help='')

        parser.add_argument('-clubid', default=None, help='', type=int)
        parser.add_argument('-max_page', default=10, help='', type=int)

        return parser.parse_args()


if __name__ == '__main__':
    # https://stackabuse.com/getting-started-with-selenium-and-python/
    SeleniumCrawler().batch()
