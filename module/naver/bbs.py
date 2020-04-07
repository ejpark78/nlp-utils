#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re
from datetime import datetime
from time import sleep
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

from module.utils.elasticsearch_utils import ElasticSearchUtils
from module.utils.logging_format import LogMessage as LogMsg
from module.utils.proxy_utils import SeleniumProxyUtils


class SeleniumCrawler(SeleniumProxyUtils):
    """웹 뉴스 크롤러 베이스"""

    def __init__(self):
        """ 생성자 """
        super().__init__()

        host = 'https://corpus.ncsoft.com:9200'
        index = 'crawler-naver-cafe'

        self.elastic = ElasticSearchUtils(
            host=host,
            index=index,
            split_index=True
        )

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
                msg = {
                    'level': 'ERROR',
                    'message': 'scroll 에러',
                    'exception': str(e),
                }
                self.logger.error(msg=LogMsg(msg))

            self.driver.implicitly_wait(10)

            sleep(5)

        return

    def save_list(self, page_list, cafe_name):
        """추출한 정보를 저장한다."""
        for doc in page_list:
            if 'cafeId' not in doc and 'articleId' not in doc:
                continue

            doc['_id'] = '{cafeId}-{articleId}'.format(**doc)

            doc['cafe_name'] = cafe_name
            doc['curl_date'] = datetime.now(self.timezone).isoformat()

            self.elastic.save_document(document=doc, delete=False)

        self.elastic.flush()

        return

    def save_contents(self, doc, flush=True, delete=False, curl_date=True, log=True):
        """추출한 정보를 저장한다."""
        if 'cafeId' not in doc and 'articleId' not in doc:
            return

        doc['_id'] = '{cafeId}-{articleId}'.format(**doc)

        if curl_date is True:
            doc['curl_date'] = datetime.now(self.timezone).isoformat()

        self.elastic.save_document(document=doc, delete=delete)
        if flush is True:
            self.elastic.flush()

        if log is True:
            try:
                msg = {
                    'level': 'MESSAGE',
                    'message': '본문 저장',
                    '_id': doc['document_id'],
                    'subject': doc['subject'],
                    'url': '{host}/{index}/_doc/{id}?pretty'.format(
                        host=self.elastic.host,
                        index=self.elastic.index,
                        id=doc['document_id'],
                    )
                }
                if 'status' in doc:
                    msg['status'] = doc['status']

                self.logger.log(level=self.MESSAGE, msg=LogMsg(msg))
            except Exception as e:
                self.logger.error(e)

        return

    def delete_post(self):
        """태그 삭제"""
        script = 'document.querySelectorAll("li.board_box").forEach(function(ele) {ele.remove();})'

        try:
            self.driver.execute_script(script)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'delete post 에러',
                'exception': str(e),
            }
            self.logger.error(msg=LogMsg(msg))

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
                msg = {
                    'level': 'ERROR',
                    'message': 'post list 에러',
                    'exception': str(e),
                }
                self.logger.error(msg=LogMsg(msg))

            query_info = self.parse_url(url=post['url'])
            for k in query_info:
                if k.find('id') < 0:
                    continue

                post[k] = int(query_info[k])

            result.append(post)

        return result

    def see_prev_reply(self):
        """ 이전 댓글 보기를 클릭한다."""
        from selenium.common.exceptions import JavascriptException

        try:
            css = 'a.cmt.next_cmt'
            self.driver.execute_script('document.querySelector("{}").click()'.format(css))

            self.wait('div.go_article a.link')
        except JavascriptException:
            return
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '다음 댓글 더보기 에러',
                'exception': str(e),
            }
            self.logger.error(msg=LogMsg(msg))
            return

        return

    def get_contents(self, result):
        """컨텐츠 하나를 조회한다."""
        self.open_driver()

        result['content'] = ''

        try:
            self.driver.get(result['url'])
            self.driver.implicitly_wait(20)
            sleep(1)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'url open 에러',
                'exception': str(e),
            }
            self.logger.error(msg=LogMsg(msg))

            result['status'] = 'url open error'
            return False

        self.see_prev_reply()
        # https://apis.naver.com/cafe-web/cafe-articleapi/cafes/27434888/articles/856012/comments?requestFrom=B&orderBy=asc&fromPopular=false

        resp_list = self.trace_networks(
            path_list=['https://apis.naver.com/cafe-web/cafe-articleapi/']
        )

        self.parse_contents_response(resp_list=resp_list, result=result)
        if 'article' in result:
            return True

        if 'status' in result and result['status'].find('error') > 0:
            return True

        self.get_html_contents(result=result)

        return True

    def parse_contents_response(self, resp_list, result):
        """ """
        if len(resp_list) == 0:
            return

        columns = {'article', 'comments', 'tags'}

        doc_list = []
        for content in resp_list:
            if self.check_history(url=content['url']) is True:
                continue

            if 'text' not in content['content']:
                continue

            item = json.loads(content['content']['text'])
            if 'menu' in item or 'message' in item:
                continue

            if 'cafeId' not in item or 'articleId' not in item:
                doc = {
                    'status': 'permission error'
                }

                result.update(doc)
                return

            if item['cafeId'] != result['cafeId'] or item['articleId'] != result['articleId']:
                continue

            doc = {k: item[k] for k in item if k in columns}

            doc_list.append(doc)

        # merge doc_list
        article_columns = {
            'id', 'refArticleId', 'subject', 'writer', 'writeDate', 'readCount', 'commentCount',
            'content', 'contentElements', 'gdid'
        }

        article = {}
        comments = []

        for doc in doc_list:
            if 'items' in doc['comments']:
                comments = doc['comments']['items']

            # shrink article
            article.update(
                {k: doc['article'][k] for k in doc['article'] if k in article_columns}
            )

            if 'content' in doc['article']:
                soup = BeautifulSoup(doc['article']['content'], 'lxml')
                article['content'] = soup.get_text(separator='\n')

        result.update({
            'article': article,
            'comments': comments
        })

        return result

    def get_html_contents(self, result):
        """ """
        try:
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html5lib')
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'parse contents 에러',
                'exception': str(e),
            }
            self.logger.error(msg=LogMsg(msg))
            return

        item = {
            'image': [],
            'content': '',
            'html_content': '',
            'bbs_name': ''.join([v.get_text().strip() for v in soup.select('div.tit_menu a span.ellip')])
        }

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
                msg = {
                    'level': 'ERROR',
                    'message': 'date parse 에러',
                    'exception': str(e),
                }
                self.logger.error(msg=LogMsg(msg))

        level = soup.select_one('div.EmptyMessageBox__content')
        if level is not None and level.get_text().find('등급') > 0:
            return

        for content in soup.select('div#postContent'):
            item['image'] += [v['src'] for v in content.find_all('img') if v.has_attr('src')]

            item['content'] += content.get_text(separator='\n').strip()
            item['html_content'] += str(content)

        reply_list = []
        for li in soup.select('div#commentArea ul li'):
            if li.has_attr('class') is False:
                continue

            reply_item = {
                'class': ' '.join(li['class']),
                'text': ''.join([v.get_text(separator='\n').strip() for v in li.select('p.txt')]),
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
                    msg = {
                        'level': 'ERROR',
                        'message': 'date parse 에러',
                        'date': reply_item['date'],
                        'exception': str(e),
                    }
                    self.logger.error(msg=LogMsg(msg))

                    del reply_item['date']
            else:
                del reply_item['date']

            reply_list.append(reply_item)

        item['reply_list'] = reply_list

        result.update(item)

        return

    def rename_doc_id(self):
        """ """
        from tqdm import tqdm

        query = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'exists': {
                                'field': 'replay_count'
                            }
                        }
                    ]
                }
            }
        }

        id_list = self.elastic.get_id_list(
            index=self.elastic.index,
            query_cond=query,
            limit=1000000,
        )
        id_list = list(id_list)

        size = 2000

        start = 0
        end = size

        while start < len(id_list):
            doc_list = []
            self.elastic.get_by_ids(
                id_list=id_list[start:end],
                index=self.elastic.index,
                source=None,
                result=doc_list
            )

            if start >= len(id_list):
                break

            start = end
            end += size

            if end > len(id_list):
                end = len(id_list)

            p_bar = tqdm(doc_list, desc='{:,}~{:,}'.format(start, end))
            for doc in p_bar:
                doc['commentCount'] = doc['replay_count']
                del doc['replay_count']

                self.save_contents(
                    doc=doc,
                    flush=False,
                    delete=True,
                    curl_date=False,
                    log=False
                )

            self.elastic.flush()

        return

    def trace_contents(self, bbs_info):
        """모든 컨텐츠를 수집한다."""
        msg = {
            'level': 'MESSAGE',
            'message': '게시글 본문 조회',
            'cafeId': bbs_info['cafeId'],
            'bbs_name': bbs_info['name']
        }
        self.logger.log(level=self.MESSAGE, msg=LogMsg(msg))

        query = {
            # 'sort': [{
            #     'date': 'desc'
            # }],
            'query': {
                'bool': {
                    'must': [
                        {
                            'match': {
                                'cafeId': bbs_info['cafeId']
                            }
                        }
                    ],
                    'must_not': [
                        {
                            'exists': {
                                'field': 'article'
                            }
                        },
                        {
                            'exists': {
                                'field': 'status'
                            }
                        },
                        {
                            'term': {
                                'subject': '벨나잇'
                            }
                        },
                        {
                            'term': {
                                'subject': '벨맛'
                            }
                        }
                    ]
                }
            }
        }

        id_list = self.elastic.get_id_list(
            index=self.elastic.index,
            query_cond=query,
            limit=self.args.limit
        )
        id_list = list(id_list)

        size = 1000

        start = 0
        end = size

        while start < len(id_list):
            doc_list = []
            self.elastic.get_by_ids(
                id_list=id_list[start:end],
                index=self.elastic.index,
                source=None,
                result=doc_list
            )

            self.open_driver()

            for i, doc in enumerate(doc_list):
                if 'cafeId' not in doc and 'articleId' not in doc:
                    continue

                msg = {
                    'level': 'MESSAGE',
                    'message': '게시글 본문 조회',
                    'current': '{:,}/{:,}'.format(i, len(doc_list)),
                    'bbs_name': bbs_info['name'],
                    'articleId': str(doc['articleId']),
                }
                self.logger.log(level=self.MESSAGE, msg=LogMsg(msg))

                self.get_contents(result=doc)

                if 'article' in doc:
                    for k in ['html_content', 'image', 'bbs_name', 'reply_list', 'nick', 'view_count', 'reply_count']:
                        if k in doc:
                            del doc[k]

                self.save_contents(doc=doc, delete=True)

                if (i + 1) % 100 == 0:
                    self.restart_driver()

                sleep(5)

            if start >= len(id_list):
                break

            start = end
            end += size

            if end > len(id_list):
                end = len(id_list)

            self.close_driver()

        return

    def restart_driver(self):
        """ """
        msg = {
            'level': 'MESSAGE',
            'message': '드라이버 재시작',
        }
        self.logger.log(level=self.MESSAGE, msg=LogMsg(msg))

        self.close_driver()
        sleep(5)
        self.open_driver()
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
                    'cafeId': club_id
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

    def parse_timestamp(self, k, timestamp):
        """ """
        k = k.replace('Timestamp', '')
        dt = datetime.fromtimestamp(timestamp / 1e3)

        return {
            k: dt.astimezone(self.timezone).isoformat()
        }

    def parse_list_response(self, resp_list):
        """ """
        if len(resp_list) == 0:
            return []

        columns = {
            'cafeId',
            'articleId',
            'refArticleId',
            'menuName',
            'subject',
            'writerId',
            'writerNickname',
            'refArticleCount',
            'readCount',
            'commentCount',
            'likeItCount',
        }

        date_columns = {
            'writeDateTimestamp',
            'lastCommentedTimestamp',
        }

        result = []
        for content in resp_list:
            if self.check_history(url=content['url']) is True:
                continue

            item = json.loads(content['content']['text'])
            if 'message' not in item:
                continue

            for item in item['message']['result']['articleList']:
                doc = {k: item[k] for k in item if k in columns}

                for k in item:
                    if k not in date_columns:
                        continue

                    doc.update(self.parse_timestamp(k, item[k]))

                result.append(doc)

        return result

    def get_article_list(self, bbs_info, continue_list=False, max_iter=2):
        """하나의 계정을 모두 읽어드린다."""
        self.open_driver()

        self.driver.get(bbs_info['url'])
        self.driver.implicitly_wait(10)

        start_article = None
        if continue_list is True:
            start_article = self.get_min_article_id(club_id=bbs_info['cafeId'])

        for i in range(max_iter):
            msg = {
                'level': 'MESSAGE',
                'message': '게시글 목록 조회',
                'current': '{:,}/{:,}'.format(i, max_iter),
                'bbs_name': bbs_info['name']
            }
            self.logger.log(level=self.MESSAGE, msg=LogMsg(msg))

            self.scroll(count=2, start_article=start_article)
            self.driver.implicitly_wait(5)

            start_article = None

            # https://apis.naver.com/cafe-web/cafe2/ArticleList.json?search.clubid=27434888&search.queryType=lastArticle&search.page=1
            resp_list = self.trace_networks(
                path_list=['https://apis.naver.com/cafe-web/cafe2/ArticleList.json']
            )

            page_list = self.parse_list_response(resp_list=resp_list)
            if len(page_list) == 0:
                page_list = self.parse_article_list_html(
                    bbs_info=bbs_info,
                    start_article=start_article
                )

            self.save_list(page_list=page_list, cafe_name=bbs_info['name'])

            # 태그 삭제
            self.delete_post()

        self.close_driver()

        return

    def parse_article_list_html(self, bbs_info, start_article):
        """하나의 계정을 모두 읽어드린다."""
        try:
            result = self.get_page_list(
                url=bbs_info['url'],
                html=self.driver.page_source
            )
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '게시글 목록 조회 에러',
                'url': bbs_info['url'],
                'exception': str(e),
            }
            self.logger.error(msg=LogMsg(msg))
            return []

        if result is None or len(result) == 0:
            return []

        if start_article is None and len(result) > 0 and 'articleid' in result[0]:
            msg = {
                'level': 'MESSAGE',
                'message': '게시글 목록 조회 성공',
                'articleid': str(result[0]['articleid'])
            }
            self.logger.log(level=self.MESSAGE, msg=LogMsg(msg))

        return result

    def batch(self):
        """"""
        self.args = self.init_arguments()

        bbs_list = self.read_config(filename=self.args.config)

        for bbs in bbs_list:
            if self.args.cafeId is not None and self.args.cafeId != bbs['cafeId']:
                continue

            bbs['url'] = bbs['url'].format(**bbs)

            if self.args.list:
                bbs['max_page'] = self.args.max_page
                if self.args.c is True:
                    bbs['max_page'] = 5000

                self.get_article_list(
                    bbs_info=bbs,
                    max_iter=bbs['max_page'],
                    continue_list=self.args.c
                )

            if self.args.contents:
                self.trace_contents(bbs_info=bbs)

        if self.args.rename_doc_id:
            self.rename_doc_id()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--config', default='./config/naver/bbs.list.json', help='')
        parser.add_argument('--user_data', default='./cache/selenium/naver-cafe', help='')

        parser.add_argument('--list', action='store_true', default=False, help='')
        parser.add_argument('--contents', action='store_true', default=False, help='')
        parser.add_argument('--rename_doc_id', action='store_true', default=False, help='')
        parser.add_argument('-c', action='store_true', default=False, help='')

        parser.add_argument('--use_head', action='store_false', default=True, help='')

        parser.add_argument('--cafeId', default=None, help='', type=int)
        parser.add_argument('--max_page', default=10, help='', type=int)

        parser.add_argument('--limit', default=-1, help='', type=int)

        parser.add_argument('--proxy_server', default='module/browsermob-proxy/bin/browsermob-proxy', help='')

        return parser.parse_args()


if __name__ == '__main__':
    # https://stackabuse.com/getting-started-with-selenium-and-python/
    SeleniumCrawler().batch()
