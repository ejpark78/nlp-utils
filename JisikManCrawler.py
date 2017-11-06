#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import os
import sys
import json

import random
import requests
import dateutil.parser

from time import sleep
from pymongo import MongoClient
from datetime import datetime
from elasticsearch import Elasticsearch
from dateutil.relativedelta import relativedelta


class JisikManCrawler:
    """
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.4.2; SAMSUNG-SM-N900A Build/KOT49H)'
        }

        self.connect = None
        self.result_db = None

        self.request_count = 0

        self.from_start = False

    @staticmethod
    def open_db(db_name='jisikman_app', host='frodo01', port=27018):
        """
        몽고 디비 핸들 오픈
        """
        connect = MongoClient('mongodb://{}:{}'.format(host, port))
        db = connect[db_name]

        return connect, db

    def curl(self, curl_url, delay=10, min_delay=6, post_data=None):
        """
        랜덤하게 기다린후 웹 페이지 크롤링, 결과는 bs4 파싱 결과를 반환
        """
        curl_url = curl_url.strip()

        # 10번에 한번씩 10초간 쉬어줌
        self.request_count += 1
        if self.request_count % 10 == 0:
            delay = 10

        # 2초 이상일 경우 랜덤하게 쉬어줌
        sleep_time = delay
        if sleep_time > min_delay:
            sleep_time = random.randrange(min_delay, delay, 1)

        # str_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # print('{}\t{} sec\t{:,}\t{}'.format(str_now, sleep_time, self.request_count, curl_url), flush=True)

        # 쉼
        sleep(sleep_time)

        # 웹 크롤링
        page_html = requests.post(curl_url, data=post_data, headers=self.headers, allow_redirects=True)

        try:
            return page_html.json()
        except Exception as err:
            print(curl_url, post_data, page_html.content, flush=True)

        return None

    @staticmethod
    def parse_time_gap(time_gap, date=None):
        """
        타임 갭을 실제 시간 문자열로 변환해서 반환
        """
        if date is None:
            date = datetime.now()

        match = re.search('(\d+)(년|달|시간|분|초) 전', time_gap)
        if match:
            gap = match.group(1)
            unit = match.group(2)

            gap = int(gap)
            if unit == '시간':
                time = date + relativedelta(hours=-gap)
            elif unit == '분':
                time = date + relativedelta(minutes=-gap)
            elif unit == '초':
                time = date + relativedelta(seconds=-gap)
            elif unit == '달':
                time = date + relativedelta(months=-gap)
            elif unit == '년':
                time = date + relativedelta(years=-gap)
            else:
                time = date

            return time.strftime("%Y-%m-%d %H:%M:%S")

        return date.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def to_simple(document):
        """
        """
        simple = None
        date = None

        try:
            dt = dateutil.parser.parse(document['date'])
            simple = {
                'document_id': document['_id'],
                'date': dt.strftime('%Y-%m-%dT%H:%M:%S'),
                'question': document['question_content'],
                'answer_list': []
            }

            if 'detail_answers' in document:
                for answer in document['detail_answers']:
                    if 'date' not in answer or answer['date'] == '':
                        answer['date'] = answer['reg_date']

                    dt = dateutil.parser.parse(answer['date'])
                    simple['answer_list'].append({
                        'content': answer['answer_content'],
                        'date': dt.strftime('%Y-%m-%dT%H:%M:%S')
                    })

            date = dateutil.parser.parse(simple['date'])
        except Exception as err:
            print('ERROR at to simple: {}'.format(sys.exc_info()[0]))

        return simple, date

    def save_elastic(self, document, host='frodo.ncsoft.com', index='jisikman'):
        """
        elastic search에 저장
        """
        simple, date = self.to_simple(document)
        if simple is None:
            return

        if simple['question'][0:2] == '[꿀':
            print('SKIP insert elastic: ', simple['question'], flush=True)
            return

        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        requests.packages.urllib3.disable_warnings(UserWarning)

        try:
            elastic = Elasticsearch([host], use_ssl=True, verify_certs=False, port=9200)
        except Exception as err:
            print('error at connect elastic', flush=True)
            return

        try:
            if elastic.indices.exists(index) is False:
                return
        except Exception as err:
            print('error at check index', flush=True)
            return

        bulk_data = [{
            'update': {
                '_type': date.year,
                '_index': index,
                '_id': simple['document_id']
            }
        }, {
            'doc': simple,
            'doc_as_upsert': True
        }]

        if self.from_start is True:
            try:
                elastic.delete(index=index, doc_type=date.year, id=simple['document_id'], refresh=True)
            except Exception as err:
                print('ERROR at delete elastic: {}'.format(sys.exc_info()[0]))

        try:
            ret = elastic.bulk(index=index, body=bulk_data, refresh=True)

            # print('elastic bulk data:', ret['errors'], flush=True)

            if ret['errors'] is True:
                print('error elastic bulk data:', ret, bulk_data, flush=True)
        except Exception as err:
            print('ERROR at save elastic: {}'.format(sys.exc_info()[0]))

        return

    def save_result(self, document, collection, upsert=False):
        """
        크롤링 결과 저장
        """
        if self.result_db is None:
            self.connect, self.result_db = self.open_db()

        if isinstance(document['_id'], str) and document['_id'].isdigit() is True:
            document['_id'] = int(document['_id'])

        answer_date = ''
        if collection is None:
            collection = 'etc'

            if 'date' in document and document['date'] != '':
                try:
                    date = dateutil.parser.parse(document['date'])
                    collection = date.strftime('%Y-%m')
                except Exception as err:
                    print('date parsing error: ', document['date'], flush=True)

            if 'detail_answers' in document and isinstance(document['detail_answers'], list) is True:
                if 'date' in document['detail_answers'][0]:
                    try:
                        answer_date = document['detail_answers'][0]['date']
                        date = dateutil.parser.parse(answer_date)
                        collection = date.strftime('%Y-%m')
                    except Exception as err:
                        print('date parsing error: ', answer_date, flush=True)

        simple_log = True
        if simple_log is True:
            if 'date' not in document:
                document['date'] = ''

            if 'question_content' in document:
                str_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                msg = '{} {:,} [{}] ({}) {}'.format(
                    str_now, int(document['_id']), answer_date, collection, document['question_content'])
                print(msg, flush=True)
        else:
            str_document = json.dumps(document, indent=3, ensure_ascii=False, sort_keys=True)
            print('save_result document:', collection, str_document, flush=True)

        if self.from_start is True:
            upsert = True

        try:
            if upsert is True:
                self.result_db.get_collection(collection).replace_one({'_id': document['_id']}, document, upsert=True)
            else:
                self.result_db.get_collection(collection).insert_one(document)
        except Exception as err:
            del document['_id']
            self.result_db.get_collection('error').insert_one(document)
            print('ERROR at save_result: {}: {}'.format(sys.exc_info()[0], document), flush=True)

            return False

        return True

    def get_last_page(self):
        """
        크롤링 상태 정보 읽기
        """
        if self.result_db is None:
            self.connect, self.result_db = self.open_db()

        cursor = self.result_db['state'].find({'_id': 'state'})[:]

        page = 0
        for document in cursor:
            page = document['page']
            break

        cursor.close()

        return page

    def query_question_list(self, from_start=False):
        """
        전체 질문 목록 크롤링
        """
        self.from_start = from_start

        start_page = 0
        end_page = 10
        if from_start is False:
            start_page = self.get_last_page()
            end_page = 100000

        print('start page: ', start_page, flush=True)

        point = 0
        for page in range(start_page, end_page):
            point, save_flag = self.query_question(page=page, point=point)
            if point is None:
                continue

            if from_start is False:
                state = {
                    '_id': 'state',
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'page': page,
                    'point': point
                }
                self.save_result(document=state, collection='state', upsert=True)
            elif save_flag is False:
                break

        return

    def query_question(self, page=0, limit=10, point=0):
        """
        하나의 질문 페이지 크롤링
        """
        q_list_url = 'http://s46.jisiklog.com/mobileapp/front/jisiktalk/GetJisiklogQuestionList_BySortOrder'

        q_post_data = {
            'content_shotage_flag': False,
            'sort_order': 'recent',
            'limit': limit,
            'point': 0,
            'page': page
        }

        q_list = self.curl(q_list_url, post_data=q_post_data)
        if q_list is None:
            return None, None

        str_q_list = json.dumps(q_list, indent=3, ensure_ascii=False, sort_keys=True)
        print('question list: ', str_q_list, flush=True)

        # 질문 목록 저장
        q_list['_id'] = '{min_point}-{point}'.format(**q_list['paging'])
        self.save_result(q_list, collection='question')

        save_flag = True
        if 'items' in q_list:
            date = datetime.now()

            for question in q_list['items']:
                flag = self.query_detail_answer(question, date)
                if flag is False:
                    save_flag = flag

        return q_list['paging']['point'], save_flag

    def query_detail_answer(self, question, date=None):
        """
        상세 답변 크롤링 
        """
        # 디폴트 date 입력
        if date is None:
            date = datetime.now()

        q_detail_url = 'http://s46.jisiklog.com/mobileapp/front/jisiktalk/GetJisiklogQuestion_detail'
        a_post_data = {
            'content_id': question['content_id']
        }

        # timegap을 날짜로 변환
        if 'timegap' in question:
            question['date'] = self.parse_time_gap(question['timegap'], date)
            del question['timegap']

        # 답변 질의
        detail = self.curl(q_detail_url, post_data=a_post_data)
        if detail is None or 'items' not in detail or detail['items'] is None:
            # 에러: 질문만 저장
            print('ERROR no items: ', detail, flush=True)
            return False

        for i, answer in enumerate(detail['items']):
            if 'answer_reg_date' in answer:
                answer['date'] = answer['answer_reg_date']
                if 'timegap' in answer:
                    del answer['timegap']
                del answer['answer_reg_date']

            if 'timegap' in answer:
                answer['date'] = self.parse_time_gap(answer['timegap'], date)
                del answer['timegap']

            if 'answer_timegap' in answer:
                del answer['answer_timegap']

            if 'date' not in question or question['date'] == '':
                if 'date' in answer and answer['date'] != '':
                    question['date'] = answer['date']
                elif 'reg_date' in answer and answer['reg_date'] != '':
                    question['date'] = answer['reg_date']

        question['_id'] = question['content_id']
        if question['_id'].isdigit() is True:
            question['_id'] = int(question['_id'])

        question['detail_answers'] = detail['items']

        # 만약 빠진 정보가 있다면 채워 넣음
        if 'answer_count' not in question:
            question['answer_count'] = len(question['detail_answers'])

        first_item = detail['items'][0]
        if 'date' not in question:
            question['date'] = first_item['date']

        if 'answer_content' not in question:
            question['answer_content'] = first_item['answer_content']

        if 'question_content' not in question:
            question['question_content'] = first_item['question_content']

        # str_q_detail = json.dumps(question, indent=3, ensure_ascii=False, sort_keys=True)
        # print('detail answer: ', str_q_detail, flush=True)

        # 질문/답변 저장
        save_flag = self.save_result(question, collection=None)
        # self.save_elastic(question)

        return save_flag

    def get_question_id_list(self, start, end):
        """
        질문 아이디 목록 반환
        """
        if self.result_db is None:
            self.connect, self.result_db = self.open_db()

        result = []
        collection_list = self.result_db.collection_names()

        # query = {'_id': {'$gte': str(start), '$lte': str(end)}}
        query = {'_id': {'$gte': start, '$lte': end}}

        for collection in collection_list:
            cursor = self.result_db.get_collection(collection).find(query, {'_id': 1})[:]

            count = 0
            for document in cursor:
                if isinstance(document['_id'], str) and document['_id'].isdigit() is not True:
                    continue

                document_id = int(document['_id'])
                if start <= document_id <= end:
                    result.append(document_id)
                    count += 1

            cursor.close()

            print(collection, query, count, flush=True)

        return sorted(result, reverse=True)

    def query_missing_question(self, start, end):
        """
        빠진 질문 아이디 수집
        """
        start = int(start.replace(',', ''))
        end = int(end.replace(',', ''))

        id_list = self.get_question_id_list(start, end)

        print('total range: {} ~ {}'.format(id_list[-1], id_list[0]), flush=True)
        for i in range(0, len(id_list)-1):
            a = id_list[i+1]
            b = id_list[i]

            if a + 1 == b:
                continue

            print('range: {:,} ~ {:,}'.format(a, b), flush=True)
            for content_id in range(a+1, b):
                # print('content_id:', content_id, flush=True)
                question = {
                    'content_id': str(content_id)
                }
                self.query_detail_answer(question)

        return

    def query_question_by_range(self, start, end):
        """
        content 아디로 질문 수집
        """
        start = int(start.replace(',', ''))
        end = int(end.replace(',', ''))

        id_list = self.get_question_id_list(start, end)

        print('range: {:,} ~ {:,}'.format(start, end), flush=True)
        print('id_list size: {:,}'.format(len(id_list)), flush=True)

        for content_id in range(start, end+1):
            if content_id in id_list:
                continue

            # print('content_id: {:,}'.format(content_id), flush=True)
            question = {
                'content_id': str(content_id)
            }
            self.query_detail_answer(question)

        return

    @staticmethod
    def parse_argument():
        """"
        옵션 설정
        """
        import argparse

        arg_parser = argparse.ArgumentParser(description='crawling web news articles')

        arg_parser.add_argument('-from_start', help='', action='store_true', default=False)
        arg_parser.add_argument('-get_missing_question', help='', action='store_true', default=False)

        arg_parser.add_argument('-query_by_id', help='', action='store_true', default=False)
        arg_parser.add_argument('-start', help='start', default="1")
        arg_parser.add_argument('-end', help='start', default="50,000") # 22,177,478

        return arg_parser.parse_args()


# end of JisikManCrawler


if __name__ == '__main__':
    crawler = JisikManCrawler()
    args = crawler.parse_argument()

    if args.get_missing_question is True:
        crawler.query_missing_question(args.start, args.end)
    elif args.query_by_id is True:
        crawler.query_question_by_range(args.start, args.end)
    else:
        crawler.query_question_list(args.from_start)


# end of __main__

# JisikManCrawler.py -from_start
# JisikManCrawler.py -get_missing_question

# range: 19,672,495 ~ 22,543,847
# range: 22,543,727 ~ 22,543,756

# ~ 22,543,853

# 22,175,000 ~ 22,180,000
# JisikManCrawler.py -query_by_id -start 22,175,000 -end 22,543,853
# JisikManCrawler.py -query_by_id -start 22,170,000 -end 22,175,000
# JisikManCrawler.py -query_by_id -start 22,160,000 -end 22,170,000
# JisikManCrawler.py -query_by_id -start 22,150,000 -end 22,160,000
# JisikManCrawler.py -query_by_id -start 22,140,000 -end 22,150,000
# JisikManCrawler.py -query_by_id -start 22,130,000 -end 22,140,000
# JisikManCrawler.py -query_by_id -start 22,120,000 -end 22,130,000
# JisikManCrawler.py -query_by_id -start 22,110,000 -end 22,120,000
# JisikManCrawler.py -query_by_id -start 22,100,000 -end 22,110,000
