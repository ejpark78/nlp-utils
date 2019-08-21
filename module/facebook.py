#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import requests

from time import sleep, time
from pymongo import MongoClient
from datetime import datetime


class Facebook(object):
    """ """

    def __init__(self):
        super().__init__()

        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        urllib3.disable_warnings(UserWarning)

        self.host = 'localhost'
        self.port = 27017

    def get_all_feed(self, page_id, access_token, db_name, collection_name):
        """ """
        i = 0
        start = datetime.now()

        # 마지막 쿼리를 가져옴
        url = None
        # url, is_done = self.get_last_request(db_name=db_name, collection_name=collection_name)
        # if is_done is True:
        #     print('Skip {}'.format(collection_name), flush=True)
        #     return True

        # 마지막 쿼리부터 가져오거나 마지막 피드를 가져와서 시작
        print('{} {} {}'.format(collection_name, page_id, start), flush=True)
        if url is not None:
            statuses = self.request_feed(url=url)
            sleep(5)
        else:
            statuses, url = self.get_last_feed(page_id=page_id, access_token=access_token, limit=10)

        # next 가 없을때까지 반복
        while True:
            self.save_data(data_list=statuses['data'], db_name=db_name, collection_name=collection_name, url=url)

            i += 1
            if i % 10 == 0:
                print('{} {}'.format(i, datetime.now()))

            # if there is no next page, we're done.
            if 'paging' in statuses.keys() and 'next' in statuses['paging']:
                url = statuses['paging']['next']

                try:
                    url_info, query = self.parse_url_query(url=url)
                    print(datetime.now(), collection_name, i, query['after'][0:10], flush=True)
                except Exception as e:
                    print(datetime.now(), collection_name, i, url, e, flush=True)

                statuses = self.request_feed(url=url)
                sleep(10)
            else:
                break

        self.save_data(data_list=None, db_name=db_name, collection_name=collection_name, url=None)
        print('완료: {} {} {}'.format(collection_name, i, datetime.now() - start), flush=True)

        return True

    def get_last_request(self, db_name, collection_name):
        """ """
        from pymongo import DESCENDING

        result = None
        is_done = False

        connect = MongoClient('mongodb://{}:{}'.format(self.host, self.port))
        db = connect.get_database(db_name)

        collection = db.get_collection(name='history-{}'.format(collection_name))

        # 히스토리 저장
        try:
            cursor = collection.find(filter={}).sort('insert_date', DESCENDING).limit(1)
            for document in cursor:
                if 'url' in document:
                    result = document['url']

                if 'is_done' in document and document['is_done'] is True:
                    is_done = True

                break

            cursor.close()
        except Exception as e:
            print('save history error: ', e, flush=True)

        connect.close()
        return result, is_done

    def test_graph_api(self, page_id, access_token):
        """ """
        url = 'https://graph.facebook.com/v2.11/{page_id}/' \
              '?access_token={access_token}'.format(page_id=page_id, access_token=access_token)

        url = 'https://graph.facebook.com/v2.11/{page_id}/feed/' \
              '?access_token={access_token}'.format(page_id=page_id, access_token=access_token)

        # retrieve data
        data = self.request_feed(url)

        print(json.dumps(data, indent=4, sort_keys=True))

        return True

    def get_last_feed(self, page_id, access_token, limit):
        """ """

        fields = [
            'caption',
            'comments{comment_count,message,like_count,message_tags,likes,reactions,parent,created_time,'
            'id,from,comments{id,like_count,comment_count,likes,parent,created_time}}',
            'created_time',
            'description',
            'from',
            'id',
            'likes.summary(true)',
            'link',
            'message',
            'name',
            'shares',
            'type',
            'with_tags'
        ]
        # 'message_tag',

        query = {
            'page_id': page_id,
            'limit': limit,
            'access_token': access_token,
            'fields': ','.join(fields),
        }

        # construct the URL string
        url = 'https://graph.facebook.com/{page_id}/feed/?' \
              'fields={fields}&limit={limit}&access_token={access_token}'.format(**query)

        return self.request_feed(url), url

    def request_feed(self, url, max_try=5, request_state=False):
        """ """
        if request_state is True:
            try:
                url_info, query = self.parse_url_query(url=url)
                print(datetime.now(), url_info.path, flush=True)
                print(json.dumps(query, indent=4, sort_keys=True), flush=True)
            except Exception as e:
                print(datetime.now(), url, e, flush=True)

        while True:
            try:
                response = requests.get(url=url, timeout=60)
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
            except Exception as e:
                print('ERROR at request {}: {}'.format(url, datetime.now()), e, flush=True)

                sleep(25)

                max_try -= 1
                if max_try < 0:
                    return None

    @staticmethod
    def parse_url_query(url):
        """ """
        from urllib.parse import urlparse, parse_qs

        query = None
        url_info = None
        try:
            url_info = urlparse(url)
            query = parse_qs(url_info.query)
        except Exception as e:
            print('error at parse url query: ', e, flush=True)

        result = {}
        if query is not None:
            for k in query:
                result[k] = query[k][0]

        return url_info, result

    def save_data(self, data_list, db_name, collection_name, url):
        """ """
        from pymongo.errors import BulkWriteError

        insert_date = datetime.now()

        # 몽고 디비 핸들 오픈
        connect = MongoClient('mongodb://{}:{}'.format(self.host, self.port))
        db = connect.get_database(db_name)

        # id 변경
        if data_list is not None:
            documents = []
            for data in data_list:
                data['_id'] = data['id']

                # 디비 저장 시간 기록
                data['insert_date'] = insert_date
                documents.append(data)

            collection = db.get_collection(name=collection_name)
            # 데이터 저장
            try:
                collection.insert_many(documents)
            except BulkWriteError as e:
                print('ERROR: ', e, e.details, flush=True)
            except Exception as e:
                print('ERROR: ', e, flush=True)

        # 히스토리 저장
        try:
            history_collection = db.get_collection(name='history-{}'.format(collection_name))

            if url is None:
                history = {
                    'is_done': True,
                    'insert_date': insert_date
                }
            else:
                history = {
                    'is_done': False,
                    'url': url,
                    'insert_date': insert_date
                }

            history_collection.insert_one(history)
        except Exception as e:
            print('ERROR history: ', e, flush=True)

        connect.close()

        return True


def main():
    # app_id = "142140609745132"
    # app_secret = "345abf6695e519ab147bee0d10d7aebb"  # DO NOT SHARE WITH ANYONE!
    #
    # access_token = '{}|{}'.format(app_id, app_secret)
    #
    # util = Facebook()
    #
    # page_list = kbo_teams + news + etc + bamboo
    # db_name = 'facebook'
    #
    # for page in page_list:
    #     collection_name, page_id = page
    #
    #     util.get_all_feed(page_id=page_id, access_token=access_token,
    #                       db_name=db_name, collection_name=collection_name)

    return True


if __name__ == "__main__":
    main()
