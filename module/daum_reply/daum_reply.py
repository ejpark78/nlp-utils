#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import requests

from time import sleep, time

from utils import Utils


class DaumReply(Utils):
    """
    """

    def __init__(self):
        super().__init__()

    def get_post_id(self, db_name='daum_sports', collection_name='2017-10'):
        """
        기사 아이디를 이용하여 post id 를 가져온다.

        :param db_name:
            디비명

        :param collection_name:
            컬랙션 이름

        :return:
            True/False
        """
        start = time()

        sleep_time = 3

        exclude_list = self.get_document_list(db_name=db_name, collection_name='post_id_{}'.format(collection_name),
                                              exclude_list=None, as_hash=False)

        document_list = self.get_document_list(db_name=db_name, collection_name=collection_name,
                                               exclude_list=exclude_list, as_hash=False)

        self.print_summary(start_time=start, tag='초기화:')
        start = time()

        url_frame = 'http://comment.daum.net/apis/v1/posts/@{article_id}'

        document_size = len(document_list)
        for i in range(document_size):
            d_id = document_list[i]
            if not d_id.isnumeric():
                continue

            # Authorization 이 헤더에 없거나 100번에 한번씩 헤더의 Authorization 갱신
            if 'Authorization' not in self.headers or i % 100 == 9:
                if self.update_header(d_id, sleep_time) is False:
                    continue

            url = url_frame.format(article_id=d_id)
            html = requests.get(url=url, headers=self.headers, timeout=10)

            # access_token 만료
            if html.status_code == 401 or html.status_code == 400:
                if self.update_header(d_id, sleep_time) is False:
                    continue

                html = requests.get(url=url, headers=self.headers, timeout=10)

            result = html.json()
            if result is None:
                continue

            if 'commentCount' not in result:
                print(d_id, html, flush=True)
                break

            print('[{:,}/{:,}]'.format(i + 1, document_size), d_id, result['id'], result['commentCount'], flush=True)

            # 진행 상황 표시
            if i > 0 and i % 9 == 0:
                self.print_summary(total=document_size, count=i+1, start_time=start, tag='진행 상황:')

            # 결과가 있다면 저장
            result['_id'] = d_id
            self.save_document(document=result, db_name=db_name,
                               collection_name='post_id_{}'.format(collection_name))

            sleep(sleep_time)

        return True

    def update_header(self, article_id, sleep_time):
        """
        해더의 Authorization 업데이트

        :return:
            True/False
        """

        access_token = self.get_access_token(article_id)
        if access_token is None:
            return False

        prev_token = ''
        if 'Authorization' in self.headers:
            prev_token = self.headers['Authorization'].split(' ', maxsplit=1)[1]

        self.headers['Authorization'] = 'Bearer {}'.format(access_token)
        print('update access token: \n-prev: \n{}\n-new: \n{}'.format(prev_token, access_token),
              file=sys.stderr, flush=True)

        sleep(sleep_time)

        return True

    def get_document_list(self, db_name, collection_name, query=None, projection=None,
                          exclude_list=None, host='frodo', port=27018, as_hash=False):
        """
        기사 아이디 목록 반환
        :param db_name:
            디비명

        :param collection_name:
            컬랙션명

        :param exclude_list:
            제외할 목록

        :param query:
            검색 조건식

        :param projection:
            반환할 필드

        :param host:
        :param port:
        :param as_hash:

        :return:
            기사 아이디 목록
        """
        if query is None:
            query = {}

        if projection is None:
            projection = {'_id': 1}

        id_only = False
        if len(projection) == 1 and projection['_id'] == 1:
            id_only = True

        connect, db = self.open_db(db_name=db_name, host=host, port=port)
        collection = db.get_collection(name=collection_name)

        if len(projection) == 0:
            cursor = collection.find(filter=query)
        else:
            cursor = collection.find(filter=query, projection=projection)

        # 결과 추출
        if as_hash is True:
            result = {}
            for d in cursor:
                result[d['_id']] = d
        else:
            if exclude_list is not None:
                if id_only is True:
                    result = [d['_id'] for d in cursor if d['_id'] not in exclude_list]
                else:
                    result = [d for d in cursor if d['_id'] not in exclude_list]
            elif id_only is True:
                result = [d['_id'] for d in cursor]
            else:
                result = [d for d in cursor]

        cursor.close()
        connect.close()

        return result

    def save_document(self, document, db_name, collection_name):
        """
        :param document:
            저장할 문서

        :param db_name:
            디비명

        :param collection_name:
            컬랙션 이름

        :return:
            True
        """
        from datetime import datetime

        connect, db = self.open_db(db_name=db_name, host='frodo', port=27018)
        collection = db.get_collection(name=collection_name)

        # 디비 저장 시간 기록
        document['insert_date'] = datetime.now()

        try:
            collection.insert_one(document)
        except Exception as e:
            print(e, flush=True)

        connect.close()
        return True

    @staticmethod
    def get_access_token(article_id):
        """
        :param article_id:
            기사에 대한 액세스 토근 추출, 다음 뉴스의 경우 액세스 토큰은 logalStorage 에 저장되어 있다.

        :reference:
            https://sites.google.com/a/chromium.org/chromedriver/downloads
            https://beomi.github.io/2017/02/27/HowToMakeWebCrawler-With-Selenium/

        :return:
            액세스 토큰
        """
        import os
        from selenium import webdriver

        url = 'http://v.sports.media.daum.net/v/{}'.format(article_id)

        options = webdriver.ChromeOptions()

        options.add_argument('headless')
        options.add_argument('window-size=800x600')

        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--no-sandbox')

        path = os.path.dirname(os.path.realpath(__file__))

        driver = webdriver.Chrome('{pwd}/chromedriver'.format(pwd=path), chrome_options=options)
        driver.implicitly_wait(3)

        driver.get(url)
        driver.implicitly_wait(3)

        try:
            client_id = driver.execute_script(
                "return document.getElementById('alex-area').getAttribute('data-client-id')")
            script = 'return localStorage.getItem("alex$bearer${}");'.format(client_id)
            item = driver.execute_script(script)

            import json
            item = json.loads(item)
        except Exception as e:
            print(e, article_id, url, file=sys.stderr, flush=True)
            return None

        driver.quit()

        return item['access_token']

    def get_reply_list(self, db_name='daum_sports', collection_name='2017-10'):
        """
        post id를 이용하여 기사에 달린 댓글을 가져온다.

        :param db_name:
            디비명

        :param collection_name:
            컬랙션 이름

        :return:
            True
        """
        start = time()

        sleep_time = 3

        exclude_list = self.get_document_list(db_name=db_name, collection_name='comments_{}'.format(collection_name))

        document_list = self.get_document_list(db_name=db_name, collection_name='post_id_{}'.format(collection_name),
                                               exclude_list=exclude_list, query={'commentCount': {'$ne': 0}},
                                               projection={'id': 1, 'commentCount': 1})

        self.print_summary(start_time=start, tag='초기화:')
        start = time()

        limit = 10

        url_frame = 'http://comment.daum.net/apis/v1/posts/{id}/comments' \
                    '?parentId=0&offset={offset}&limit={limit}&sort=RECOMMEND'

        document_size = len(document_list)
        for i in range(document_size):
            d_id = document_list[i]['_id']
            post_id = document_list[i]['id']
            comment_count = document_list[i]['commentCount']

            print('[{:,}/{:,}]'.format(i + 1, document_size), d_id, post_id, comment_count, end=' ', flush=True)

            result = self.get_one_replay(url_frame=url_frame, post_id=post_id, total=comment_count,
                                         limit=limit, sleep_time=sleep_time)

            # 진행 상황 표시
            if i > 0 and i % 9 == 0:
                self.print_summary(total=document_size, count=i + 1, start_time=start, tag='진행 상황:')

            # 결과가 있다면 저장
            document = {
                '_id': d_id,
                'id': post_id,
                'comment_list': result
            }
            self.save_document(document=document, db_name=db_name,
                               collection_name='comments_{}'.format(collection_name))

        return True

    def get_reply_children(self, db_name='daum_sports', collection_name='2017-10'):
        """
        댓글의 댓글 크롤링
        :param db_name:
            디비명

        :param collection_name:
            컬랙션 이름

        :return:
            True/False
        """
        start = time()

        sleep_time = 3

        exclude_list = self.get_document_list(db_name=db_name,
                                              collection_name='children_comments_{}'.format(collection_name))

        query = {
            'comment_list': {
                '$elemMatch': {
                    'childCount': {'$ne': 0}
                }
            }
        }
        document_list = self.get_document_list(db_name=db_name,
                                               collection_name='comments_{}'.format(collection_name),
                                               query=query, projection={})

        self.print_summary(start_time=start, tag='초기화:')
        start = time()

        limit = 10

        url_frame = 'http://comment.daum.net/apis/v1/comments/{id}/children' \
                    '?offset={offset}&limit={limit}&sort=LATEST'

        document_size = len(document_list)
        for i in range(document_size):
            d_id = document_list[i]['_id']
            parent_id = document_list[i]['id']

            comment_list = document_list[i]['comment_list']
            comment_size = len(comment_list)
            for j in range(comment_size):
                reply = comment_list[j]
                if reply['childCount'] == 0:
                    continue

                post_id = reply['id']
                total = reply['childCount']

                if post_id in exclude_list:
                    continue

                print('[{:,}/{:,}, {:,}/{:,}]'.format(i + 1, document_size, j + 1, comment_size),
                      d_id, post_id, reply['childCount'], end=' ', flush=True)

                result = self.get_one_replay(url_frame=url_frame, post_id=post_id, total=total,
                                             limit=limit, sleep_time=sleep_time)

                # 결과가 있다면 저장
                document = {
                    '_id': post_id,
                    'article_id': d_id,
                    'parentId': parent_id,
                    'comment_list': result
                }
                self.save_document(document=document, db_name=db_name,
                                   collection_name='children_comments_{}'.format(collection_name))
            # 진행 상황 표시
            if i > 0 and i % 9 == 0:
                self.print_summary(total=document_size, count=i + 1, start_time=start, tag='진행 상황:')

        return True

    def get_one_replay(self, url_frame, post_id, total, limit, sleep_time):
        """
        :return:
            댓글 목록 반환
        """
        result = []
        for offset in range(0, total, limit):
            url = url_frame.format(id=post_id, offset=offset, limit=limit)

            html = requests.get(url=url, headers=self.headers, timeout=10)
            result += html.json()

            print('{:,},'.format(offset), end='', flush=True)

            sleep(sleep_time)

        print('{:,}'.format(len(result)), flush=True)
        return result

    def export_replay(self):
        """
        :return:
        """
        start = time()

        db_name = 'daum_sports'
        collection_name = '2017-10'

        document_list = self.get_document_list(db_name=db_name, collection_name='post_id_{}'.format(collection_name),
                                               query={'commentCount': {'$ne': 0}}, projection={}, as_hash=True)

        comment_list = self.get_document_list(db_name=db_name, collection_name='comments_{}'.format(collection_name),
                                              query={}, projection={}, as_hash=True)

        self.print_summary(start_time=start, tag='초기화:')
        start = time()

        document_title = ['_id', 'id', 'url', 'title', 'description']
        reply_title = ['likeCount', 'dislikeCount', 'recommendCount', 'childCount', 'content']

        print('\t'.join(document_title+reply_title), flush=True)

        for d_id in comment_list:
            reply_list = comment_list[d_id]['comment_list']
            document = document_list[d_id]

            doc_buf = self._get_data(document, document_title)
            if doc_buf is None:
                continue

            for reply in reply_list:
                buf = self._get_data(reply, reply_title)
                if buf is None:
                    continue

                buf = doc_buf + buf
                print('\t'.join(buf), flush=True)

        return True

    @staticmethod
    def _get_data(data, key_list):
        """
        :param data:
        :param key_list:
        :return:
        """
        result = []
        for k in key_list:
            if k not in data:
                return None

            if isinstance(data[k], str):
                data[k] = data[k].replace('\t', ' ')
                data[k] = data[k].replace('\r\n', '<br>')
                data[k] = data[k].replace('\n', '<br>')

            result.append('{}'.format(data[k]))

        return result

    def update_article_id(self):
        """
        기사 아이디가 잘못된 경우 변경

        :return:
            True
        """
        db_name = 'daum_sports'
        host = 'frodo'
        port = 27018
        collection_name = '2017-10'

        connect, db = self.open_db(db_name=db_name, host=host, port=port)
        collection = db.get_collection(name=collection_name)

        query = {'_id': {'$regex': 'daum'}}
        cursor = collection.find(filter=query)[:]

        import re

        for document in cursor:
            # prev_id = document['_id']
            document['_id'] = re.sub(r'^.+\.', '', document['_id'])

            # collection.insert(document)
            # collection.delete_one({'_id': prev_id})
            print(document)

        cursor.close()
        connect.close()

        return True


def init_arguments():
    """
    옵션 설정

    :return:
        parsed arguments
    """
    import argparse

    parser = argparse.ArgumentParser(description='daum 댓글 크롤러')

    parser.add_argument('-db_name', default='daum_sports', help='디비명')
    parser.add_argument('-collection', default='2017-10', help='컬랙션 이름')

    parser.add_argument('-get_post_id', action='store_true', default=False,
                        help='컬랙션에 저장된 모든 신문기사의 post id 수집')
    parser.add_argument('-get_reply_list', action='store_true', default=False,
                        help='모든 post id 의 댓글 수집')
    parser.add_argument('-get_reply_children', action='store_true', default=False,
                        help='댓글의 댓글 수집')

    return parser.parse_args()


def main():
    args = init_arguments()

    util = DaumReply()

    # util.update_article_id()

    collection_list = ['2017-10', '2017-09', '2017-08', '2017-07', '2017-06',
                       '2017-05', '2017-04', '2017-03', '2017-02', '2017-01']

    for collection in collection_list:
        if args.get_post_id:
            util.get_post_id(db_name=args.db_name, collection_name=collection)

        if args.get_reply_list:
            util.get_reply_list(db_name=args.db_name, collection_name=collection)

        if args.get_reply_children:
            util.get_reply_children(db_name=args.db_name, collection_name=collection)

    # util.export_replay()

    return True


if __name__ == "__main__":
    main()
