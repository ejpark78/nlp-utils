#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
from datetime import datetime
from time import sleep
from urllib.parse import urljoin

import pytz
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from tqdm.autonotebook import tqdm

from crawler.utils.elasticsearch_utils import ElasticSearchUtils

MESSAGE = 25
logging_opt = {
    'format': '[%(levelname)-s] %(message)s',
    'handlers': [logging.StreamHandler()],
    'level': MESSAGE,

}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)


class LineageMBBSJap(object):
    """크롤러"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        host_info = {
            'host': 'https://corpus.ncsoft.com:9200',
            'index': 'crawler-bbs-game-lineagem-jap',
            'http_auth': 'crawler:crawler2019',
            'split_index': True,
        }

        self.elastic = ElasticSearchUtils(**host_info)

        self.timezone = pytz.timezone('Asia/Seoul')

    @staticmethod
    def get_article_list(page):
        """ """
        url = 'https://www.ncsoft.jp/lineage2/community/lineage2Board/list?currentPage={page}'.format(page=page)

        resp = requests.get(url, verify=False)
        soup = BeautifulSoup(resp.text, 'html5lib')

        result = []
        for tag in soup.select('table.article_list tr'):
            td_tags = tag.select('td')
            if len(td_tags) == 0:
                continue

            doc = {
                '_id': int(td_tags[0].get_text().strip()),
                'title': ''.join([v.get_text().strip() for v in tag.select('td.cell_subject')]).split('\n')[0],
                'url': ''.join(
                    [urljoin(url, v['href']) for v in tag.select('td.cell_subject a') if v.has_attr('href')]),
                'author': ''.join([v.get_text().strip() for v in tag.select('td.cell_author')]),
                'views': int(td_tags[-2].get_text().strip()),
                'likes': int(td_tags[-2].get_text().strip()),
            }

            result.append(doc)

        return result

    def get_article(self, url):
        """ """
        resp = requests.get(url, verify=False)
        soup = BeautifulSoup(resp.text, 'html5lib')

        soup.select('div.post_view')

        post_view = soup.select_one('div.post_view')
        if post_view is None:
            return []

        dt = ''.join([v.get_text().strip() for v in post_view.select('div.view_header span.post_datetime')])

        view_body = post_view.select_one('div.view_body')

        result = {
            'title': ''.join([v.get_text().strip() for v in post_view.select('div.view_header div.title')]),
            'date': parse_date(dt).astimezone(self.timezone).isoformat(),
            'content': view_body.get_text().strip(),
            'html_content': str(view_body),
        }

        reply_list = []
        for reply in soup.select('ul.cmt_list li.cmt_block'):
            dt_tag = ''.join([v.get_text().strip() for v in reply.select('div.cmt_author span.cmt_datetime')])

            dt = ''
            try:
                dt = parse_date(dt_tag).astimezone(self.timezone).isoformat()
            except Exception as e:
                pass

            item = {
                'author': ''.join([v.get_text().strip() for v in reply.select('div.cmt_author em.tpoint1')]),
                'date': dt,
                'content': ''.join([v.get_text().strip() for v in reply.select('div.cmt_content')]),
            }
            reply_list.append(item)

        result['reply_list'] = reply_list

        return result

    def batch(self):
        """ """
        pbar = tqdm(range(1, 1539))

        for page in pbar:
            pbar.set_description('page: {:,}'.format(page))

            doc_list = self.get_article_list(page=page)
            sleep(3)

            for doc in doc_list:
                article = self.get_article(url=doc['url'])
                doc.update(article)

                doc['curl_date'] = datetime.now(self.timezone).isoformat()

                self.elastic.save_document(document=doc, delete=False)
                self.elastic.flush()

                sleep(3)
        return


if __name__ == '__main__':
    LineageMBBSJap().batch()
