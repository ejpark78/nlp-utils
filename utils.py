#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""웹 크롤링에 필요한 유틸"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
import json
import logging
import os
import queue
import random
import re
from datetime import datetime
from time import sleep
from urllib.parse import urljoin

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class Utils(object):
    """ 크롤러 유틸 """

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/62.0.3202.75 Safari/537.36'
        }

        self.job_info = None

        self.hostname = None
        self.request_count = 0

        # 저장 큐
        self.mutex = False
        self.job_queue = queue.Queue()

        self.debug_mode = False

        self.bulk_data = []

    @staticmethod
    def replace_tag(html_tag, tag_list, replacement='', attribute=None):
        """ html 태그 중 특정 태그를 삭제한다. ex) script, caption, style, ...

        :param html_tag: html 본문
        :param tag_list: 제거할 태그 목록
        :param replacement: 치환할 문자
        :param attribute: 특정 속성값 포함 여부
        :return: True/False
        """
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
        """ html 태그 중에서 주석 태그를 제거한다.

        :param soup: 웹페이지 본문
        :return: True/False
        """
        from bs4 import Comment

        for element in soup(text=lambda text: isinstance(text, Comment)):
            element.extract()

        return True

    @staticmethod
    def get_encoding_type(html_body):
        """ 메타 정보에서 인코딩 정보 반환한다.

        :param html_body: html 본문
        :return: BeautifulSoup 반환
        """
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
    def get_url(url, url_type=None):
        """ url 문자열을 찾아서 반환한다.

        :param url: url 구조체
        :param url_type: url 타입 명시
        :return: url
        """

        if url_type is not None and url_type in url:
            return url[url_type]

        if isinstance(url, str) is True:
            return url
        elif 'simple' in url and url['simple'] != '':
            return url['simple']
        elif 'full' in url:
            return url['full']

        return ''

    def curl_html(self, curl_url, delay='6~9', post_data=None, json_type=False,
                  encoding=None, max_try=3, headers=None, html_parser=None):
        """랜덤하게 기다린후 웹 페이지 크롤링, bs4 파싱 결과를 반환한다.

        :param curl_url: 받아올 URL 주소
        :param delay: delay 범위: 10~15, 10초에서 15초 사이
        :param post_data: post 방식으로 보낼때 data
        :param json_type: json 결과 형식 명시
        :param encoding: 인코딩 명시
        :param max_try: 최대 시도 횟수 명시
        :param headers: 헤더 명시
        :param html_parser: html 파서 명시
        :return: 크롤링 결과 반환, html or json 형식으로 반환
        """
        # 디폴트 범위
        min_delay = 10
        max_delay = 15

        if '~' in delay:
            min_delay, max_delay = delay.split('~', maxsplit=1)

            min_delay = int(min_delay)
            max_delay = int(max_delay)

        curl_url = self.get_url(curl_url, url_type='full')
        curl_url = curl_url.strip()

        if curl_url == '' or curl_url.find('http') != 0:
            logging.warning(msg='다운 받을 url 이 없음: {}'.format(curl_url))
            return

        # 2초 이상일 경우 랜덤하게 쉬어줌
        sleep_time = min_delay
        if sleep_time > max_delay:
            sleep_time = random.randrange(min_delay, max_delay, 1)

        # 10번에 한번씩 60초간 쉬어줌
        self.request_count += 1
        if self.request_count % 60 == 0:
            sleep_time = 60 + max_delay

        # 상태 출력
        if self.debug_mode is True:
            sleep_time = int(os.getenv('SLEEP', 1))

        logging.info(msg='크롤러 sleep: {} secs'.format(sleep_time))
        sleep(sleep_time)

        # 해더 생성
        if headers is None:
            headers = self.headers
        else:
            headers.update(self.headers)

        # 웹 크롤링
        try:
            if post_data is None:
                page_html = requests.get(url=curl_url, headers=headers,
                                         allow_redirects=True, timeout=60)
            else:
                page_html = requests.post(url=curl_url, data=post_data, headers=self.headers,
                                          allow_redirects=True, timeout=60)
        except Exception as e:
            logging.error(msg='requests 에러: {} {}'.format(curl_url, e))
            return None

        # json_type 일 경우
        if json_type is True:
            try:
                result = page_html.json()
            except Exception as e:
                logging.error(msg='json 추출 에러: {}'.format(e))

                if page_html.content == b'':
                    return None

                if max_try > 0:
                    if self.debug_mode is False:
                        logging.error(msg='최대 크롤링 시도 횟수 초과: {}'.format(curl_url))
                        sleep(sleep_time * 10)
                    else:
                        sleep_time = int(os.getenv('SLEEP', 1))
                        sleep(sleep_time)

                    return self.curl_html(curl_url=curl_url, delay=delay, post_data=post_data,
                                          html_parser=html_parser, json_type=json_type, encoding=encoding,
                                          max_try=max_try - 1)
                else:
                    logging.error(msg='크롤링 에러')
                    raise

            return result

        # post 로 요청했을 때 바로 반환
        if post_data is not None:
            return page_html

        # 인코딩 변환이 지정되어 있은 경우 인코딩을 변경함
        soup = None
        content = page_html.text
        if encoding is None:
            soup, encoding = self.get_encoding_type(content)

        if encoding is not None:
            content = page_html.content
            content = content.decode(encoding, 'ignore')

        # html 일 경우
        try:
            from bs4 import BeautifulSoup

            if soup is not None and encoding is None:
                return soup

            # lxml is the faster parser and can handle broken HTML quite well,
            # html5lib comes closest to how your browser would parse broken HTML but is a lot slower.
            # lxml

            if html_parser is None:
                return BeautifulSoup(content, 'html5lib')
            else:
                return BeautifulSoup(content, html_parser)
        except Exception as e:
            logging.error(msg='html 파싱 에러: {}'.format(e))

        return None

    def parse_html(self, article, soup, target_tags, article_list):
        """ html 파싱, 지정된 태그에서 정보를 추출한다.

        :param article: 신문 기사 문서
        :param soup: soup 개체
        :param target_tags: 찾는 태그 정보
        :param article_list: 기사 목록
        :return:
        """
        url = self.get_url(article['url'])

        for tag_info in target_tags:
            try:
                self.get_target_value(soup, tag_info, article_list, url)
            except Exception as e:
                logging.error(msg='크롤링 결과 피싱 에러: {} {}'.format(url, e))
                return None

        for item in article_list:
            for key in item:
                article[key] = item[key]

        return article

    @staticmethod
    def get_date_collection_name(date):
        """ 날짜와 컬랙션 이름을 변환한다.

        :param date: 날짜 문자열
        :return: 날짜와 컬랙션 이름
        """
        from dateutil.parser import parse as parse_date
        from dateutil.relativedelta import relativedelta

        collection = 'error'
        if isinstance(date, str) is True:
            try:
                # 상대 시간 계산
                if '일전' in date:
                    offset = int(date.replace('일전', ''))
                    date = datetime.now()
                    date += relativedelta(days=-offset)
                elif '분전' in date:
                    offset = int(date.replace('분전', ''))
                    date = datetime.now()
                    date += relativedelta(minutes=-offset)
                elif '시간전' in date:
                    offset = int(date.replace('시간전', ''))
                    date = datetime.now()
                    date += relativedelta(hours=-offset)
                else:
                    date = parse_date(date)

                collection = date.strftime('%Y-%m')
            except Exception as e:
                logging.error(msg='날짜 파싱 에러: {} {}'.format(date, e))
                return None, collection
        elif isinstance(date, dict) is True:
            if 'date' in date:
                collection = '{}-{}'.format(date['year'], date['month'])
        elif isinstance(date, datetime) is True:
            collection = date.strftime('%Y-%m')

        return date, collection

    @staticmethod
    def open_db(db_name, host='gollum', port=27017):
        """ 몽고 디비에 연결한다.

        :param db_name: 데이터베이스명
        :param host: 서버 주소
        :param port: 서버 포트
        :return: 접속 정보와 데이터베이스 핸들
        """
        from pymongo import MongoClient

        connect = None
        try:
            connect = MongoClient('mongodb://{}:{}'.format(host, port))
        except Exception as e:
            logging.error(msg='{}'.format(e))

        db = None
        if connect is not None:
            db = connect.get_database(db_name)

        return connect, db

    @staticmethod
    def get_document_id(url):
        """ url 주소를 문서 아이디로 변환하여 반환한다.

        :param url: url 주소
        :return: 문서 아이디
        """
        document_id = []

        #  http://sports.news.nate.com/view/20160701n35320
        # "score.sports.media.daum.planus.api.v2.api.hermes.sports_game_related_contents.json.game_id.71041101.op_key.sportsSummary,gameCenter.sort_order.VIEW_ASC.page_count.1.page_size.100"
        stop_word = ['http', 'https', 'com', 'co', 'kr', 'view', 'nhn', 'read', 'main', 'net', 'newsview', 'php',
                     'm', 'b', 'api', 'hermes', 'json', 'op_key', 'sort_order', 'VIEW_ASC', 'page_count', 'page_size',
                     'v2', 'planus', 'proxy', 'sort-by', 'orderSequence$desc$int', 'ronaldo', 'gallery', 'VIEW_DESC',
                     'sports_game_related_contents', 'aspx', 'www', 'html', 'site', 'html_dir', 'data', 'asp',
                     'related_all', 'reuters', 'article']

        url = url.replace('&amp;', '&')

        for ch in ['/', '.', ':', '?', '=', '&', '#', '|', ',']:
            url = url.replace(ch, ' ')

        for token in url.split(' '):
            if token == '' or token in stop_word:
                continue

            document_id.append(token)

        return '.'.join(document_id)

    @staticmethod
    def _json_serial(obj):
        """ json.dumps 의 콜백 함수로 넘겨주는 함수이다. 날자 형식을 문자로 반환한다.

        :param obj: 기사 문서 아이템
        :return:
        """
        from datetime import datetime

        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')

        raise TypeError("Type not serializable")

    def send_kafka_message(self, document, kafka_info, mongodb_info):
        """ kafka 에 메세지를 전송한다.

        :param document: 기사 본문
        :param kafka_info:
            카프카 접속 정보::

                "kafka": {
                  "host": "gollum",
                  "result": {
                    "elastic": {
                      "type": "2017-11",
                      "host": "frodo",
                      "index": "naver_society",
                      "update": true
                    }
                  },
                  "job_id": "crawler_naver_society_2017",
                  "port": 9092,
                  "topic": "crawler"
                }

        :param mongodb_info: 몽고 디비 정보, collection 명과 일치
        :return: True/False

        콘솔에서 디버깅 방법::

            $ kafka-topics.sh --list --zookeeper gollum:2181
            $ kafka-console-consumer.sh --bootstrap-server gollum:9092 --topic crawler --from-beginning

        """
        try:
            from kafka import KafkaProducer
        except ImportError:
            logging.error(msg='kafka import error')
            return False

        if 'port' not in kafka_info:
            kafka_info['port'] = 9092

        try:
            producer = KafkaProducer(
                bootstrap_servers='{}:{}'.format(kafka_info['host'], kafka_info['port']),
                compression_type='gzip'
            )

            # 크롤러 메타 정보 저장
            document['crawler_meta'] = kafka_info
            if self.job_info is not None:
                document['crawler_meta']['job_id'] = self.job_info['_id']

                if 'result' in document['crawler_meta']:
                    result_info = document['crawler_meta']['result']

                    if 'elastic' in result_info:
                        result_info['elastic']['type'] = mongodb_info['collection']

            message = json.dumps(document, ensure_ascii=False, default=self._json_serial)

            producer.send(kafka_info['topic'], bytes(message, encoding='utf-8')).get(timeout=5)
            producer.flush()
        except Exception as e:
            logging.error(msg='카프카 에러: {} {}'.format(kafka_info['topic'], e))

        return True

    def send_mqtt_message(self, document, mqtt_info):
        """ mqtt로 크롤링 메세지를 전송한다.

        :param document: 기사 본문
        :param mqtt_info: mqtt 서버 접속 정보
        :return: True/False
        """
        try:
            import paho.mqtt.publish as publish
        except ImportError:
            logging.error(msg='paho.mqtt import error')
            return False

        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # mqtt 에 메세지 전송
        if self.hostname is None:
            self.hostname = os.uname()[1]
            self.hostname = self.hostname.split('-')[0]

        payload = {
            'host': self.hostname,
            'now': str_now,
            'db_name': mqtt_info['name'],
            'collection': mqtt_info['collection'],
            'title': document['_id'],
            'document_id': document['_id']
        }

        if self.job_info is not None:
            payload['job_id'] = self.job_info['_id']

            job_id = payload['job_id'].replace('-', '_')
            token = job_id.split('_')
            if len(token) > 2:
                payload['source'] = token[1]
                payload['section'] = token[2]

            if len(token) > 3:
                payload['tag'] = '_'.join(token[3:])

        if 'title' in document:
            payload['title'] = document['title']

        if 'date' in document and isinstance(document['date'], datetime) is True:
            payload['date'] = document['date'].strftime('%Y-%m-%d')

        str_payload = json.dumps(payload, ensure_ascii=False, indent=4)

        try:
            if 'port' not in mqtt_info:
                mqtt_info['port'] = 1883

            publish.single(
                topic=mqtt_info['topic'],
                payload=str_payload, qos=2,
                hostname=mqtt_info['host'], port=mqtt_info['port'],
                client_id='')
        except Exception as e:
            logging.error(msg='mqtt 에러: {}'.format(e))

        return True

    @staticmethod
    def create_elastic_index(elastic, index_name=None):
        """ elastic-search 에 인덱스를 생성한다.

        :param elastic: elastic 서버 접속 정보
        :param index_name: 생성할 인덱스 이름
        :return: True/False
        settings 정보:
            * 'number_of_shards': 샤딩 수
            * 'number_of_replicas': 리플리카 수
            * 'index.mapper.dynamic': mapping 자동 할당
        """
        if elastic is None:
            return False

        elastic.indices.create(
            index=index_name,
            body={
                'settings': {
                    'number_of_shards': 3,
                    'number_of_replicas': 2,
                    'index.mapper.dynamic': True
                }
            }
        )

        return True

    @staticmethod
    def convert_datetime(document):
        """ 입력받은 문서에서 데이터 타입이 datetime 를 문자열로 변환한다.

        :param document: 문서
        :return: 변환된 문서
        """

        for k in document:
            item = document[k]

            if isinstance(item, datetime):
                document[k] = item.strftime('%Y-%m-%dT%H:%M:%S')

        return document

    def save_mongodb(self, document, mongodb_info, db_name, update):
        """ 몽고 디비에 문서를 저장

        :param document: 저장할 문서
        :param mongodb_info:
            몽고 디비 접속 정보::

                "mongo": {
                    "port": 27018,
                    "update": false,
                    "host": "frodo",
                }

        :param db_name: 저장할 디비 이름
        :param update: 내용 갱신 여부 (True/False)
        :return: True/False
        """
        from pymongo import errors

        if document is None:
            return False

        if '_id' not in document:
            url = self.get_url(document['url'])
            document['_id'] = self.get_document_id(url)

        port = 27017
        if 'port' in mongodb_info:
            port = mongodb_info['port']

        collection_name = None
        if 'collection' in mongodb_info:
            collection_name = mongodb_info['collection']

        if 'update' in mongodb_info:
            update = mongodb_info['update']

        if 'name' in mongodb_info:
            db_name = mongodb_info['name']

        meta = {}
        if 'meta' in document:
            for k in document['meta']:
                if k.find('.') >= 0:
                    meta[k.replace('.', '_')] = document['meta'][k]
                    continue

                meta[k] = document['meta'][k]

            document['meta'] = meta

        # 디비 연결
        connect, mongodb = self.open_db(host=mongodb_info['host'],
                                        db_name=db_name, port=port)

        # 몽고 디비에 문서 저장
        query = {'_id': document['_id']}
        try:
            collection = mongodb.get_collection(collection_name)

            # update 모드인 경우 문서를 새로 저장
            if update is True:
                collection.replace_one(query, document, upsert=True)
            else:
                collection.insert_one(document)
        except errors.DuplicateKeyError:
            msg = '몽고디비 키 중복 에러: {} {}'.format(collection_name, document['_id'])
            logging.error(msg=msg)
        except Exception as e:
            msg = '몽고디비 저장 에러: {} {} {}'.format(collection_name, document['_id'], e)
            logging.error(msg=msg)

            # 저장에 실패할 경우 error 컬랙션에 저장
            try:
                collection = mongodb.get_collection('error')

                if '_id' in document:
                    collection.replace_one(query, document, upsert=True)
                else:
                    collection.insert_one(document)
            except Exception as e:
                logging.error(msg='error 컬랙션에 저장 에러: {}'.format(e))

            return False

        # 연결 종료
        connect.close()

        # 섹션 정보 저장
        if 'section' in document:
            self.save_section_info(document=document, mongodb_info=mongodb_info, db_name=db_name,
                                   collection_name='section_{}'.format(collection_name))

        # 현재 상황 출력
        msg = [mongodb_info['host'], db_name, collection_name]
        for key in ['_id', 'date', 'section', 'title', 'url']:
            if key not in document:
                continue

            if isinstance(document[key], str):
                msg.append(document[key])
                continue

            if isinstance(document[key], datetime):
                msg.append(document[key].strftime('%Y-%m-%d %H:%M:%S'))

        if len(msg) > 0:
            logging.info(msg='몽고디비 저장 정보: {}'.format('\t'.join(msg)))

        return True

    def save_logs(self, document, elastic_info, mongodb_info):
        """ 엘라스틱서치에 로그 저장

        :param document: 크롤링 결과 문서
        :param elastic_info: elastic 접속 정보
        :param mongodb_info: 몽고 디비 접속 정보: collection 이름 사용
        :return: True/False
        """
        from elasticsearch import Elasticsearch

        # 타입 추출, 몽고 디비 collection 이름 우선
        index_type = mongodb_info['name']
        if 'type' in elastic_info and elastic_info['type'] is not None:
            index_type = elastic_info['type']

        # 날짜 변환
        if 'date' in document and isinstance(document['date'], datetime):
            document['date'] = document['date'].strftime('%Y-%m-%dT%H:%M:%S')
        else:
            return False

        payload = {
            'host': self.hostname,
            'insert_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'mongo': {
                'host': mongodb_info['host'],
                'name': mongodb_info['name'],
                'collection': mongodb_info['collection']
            },
            'title': document['_id'],
            'date': document['date'],
            'document_id': document['_id']
        }

        bulk_data = [{
            'update': {
                '_index': elastic_info['index'],
                '_type': index_type,
                '_id': payload['document_id']
            }
        }, {
            'doc': payload,
            'doc_as_upsert': True
        }]

        # 서버 접속
        elastic = None
        try:
            elastic = Elasticsearch(hosts=[elastic_info['host']], timeout=30)

            if elastic.indices.exists(elastic_info['index']) is False:
                self.create_elastic_index(elastic, elastic_info['index'])
        except Exception as e:
            logging.error(msg='elastic-search 접속 에러: {}'.format(e))

        if elastic is None:
            return False

        # 문서 저장
        try:
            elastic.bulk(index=elastic_info['index'], body=bulk_data, refresh=True)
        except Exception as e:
            logging.error(msg='elastic-search 저장 에러: {}'.format(e))

        return True

    def send_corpus_process(self, document, api_info, db_name, update):
        """ 코퍼스 저처리 분석 데몬에 문서 아이디 전달

        :param document: 전달할 문서
        :param api_info: 전처리 API 서버 정보
        :param db_name: 디비명
        :param update: 디비 갱신 여부 (True/False)
        :return: True/False
        """
        if document is None:
            return False

        # 필수 항목: url
        # 선택: index, type
        index, doc_type = self.get_elastic_index_info(db_name=db_name, elastic_info=api_info,
                                                      article_date=document['date'])

        if index is None or doc_type is None:
            return

        # 날짜 변환
        document = self.convert_datetime(document=document)

        if 'update' in api_info:
            update = api_info['update']

        body = {
            'index': index,
            'update': update,
            'doc_type': doc_type,
            'document': document
        }

        headers = {'Content-Type': 'application/json'}
        try:
            url = api_info['host']
            requests.post(url=url, json=body, headers=headers,
                          allow_redirects=True, timeout=30, verify=False)

            msg = '코퍼스 전처리: {} {} {}'.format(url, document['_id'], document['title'])
            logging.info(msg=msg)
        except Exception as e:
            msg = '코퍼스 전처리 에러: {} {}'.format(document['_id'], e)
            logging.error(msg=msg)

        return True

    def save_elastic(self, document, elastic_info, db_name, insert, bulk_size=0):
        """elastic search 에 문서를 저장한다.

        :param document: 저장할 문서
        :param elastic_info:
            elastic 접속 정보::

                {
                  "host": "http://nlpapi.ncsoft.com:9200",
                  "index": None,
                  "type": None,
                  "insert": true
                }

        :param db_name: 디비 이름
        :param insert: 디비 삽입 여부 (True/False)
        :param bulk_size: elastic-search 한번에 저장할 크기
        :return: True/False
        """
        from elasticsearch import Elasticsearch

        if document is not None and 'date' in document:
            article_date = document['date']
        else:
            article_date = datetime.now()

        # 인덱스 추출, 몽고 디비 collection 이름 우선
        index, doc_type = self.get_elastic_index_info(db_name=db_name, elastic_info=elastic_info,
                                                      article_date=article_date)

        if index is None or doc_type is None:
            logging.error(msg='index or doc_type is None: {} {}'.format(index, doc_type))
            return False

        if 'insert' in elastic_info:
            insert = elastic_info['insert']

        # 입력시간 삽입: 코퍼스 전처리에서 삽입
        # document['insert_date'] = datetime.now()

        if document is not None:
            # 날짜 변환
            document = self.convert_datetime(document=document)

            if '_id' in document:
                document['document_id'] = document['_id']
                del document['_id']
            else:
                document['document_id'] = datetime.now().strftime('%Y%m%d_%H%M%S.%f')

            self.bulk_data.append({
                'update': {
                    '_index': index,
                    '_type': doc_type,
                    '_id': document['document_id']
                }
            })

            self.bulk_data.append({
                'doc': document,
                'doc_as_upsert': insert
            })

            # 버퍼링
            if bulk_size > len(self.bulk_data):
                return True

        if len(self.bulk_data) == 0:
            return True

        # 서버 접속
        elastic = None
        try:
            elastic = Elasticsearch(hosts=[elastic_info['host']], timeout=30)

            if elastic.indices.exists(index) is False:
                self.create_elastic_index(elastic, index)
        except Exception as e:
            logging.error(msg='elastic-search 접속 에러: {}'.format(e))

        if elastic is None:
            return False

        # 문서 저장
        try:
            response = elastic.bulk(index=index, body=self.bulk_data, refresh=True)

            size = len(self.bulk_data)
            doc_id_list = []
            for doc in self.bulk_data:
                doc_id_list.append(doc['update']['_id'])

            self.bulk_data = []

            error = '성공'
            if response['errors'] is True:
                error = '에러'

            msg = 'elastic-search 저장 결과: {}, {:,}'.format(error, size)
            logging.info(msg=msg)

            msg = '{}/{}/{}/{}?pretty'.format(elastic_info['host'], index, doc_type, doc_id_list[0])
            logging.info(msg=msg)
        except Exception as e:
            msg = 'elastic-search 저장 에러: {}'.format(e)
            logging.error(msg=msg)

        return True

    @staticmethod
    def get_tag_text(tag):
        """
        텍스트 반환
        :param tag: HTML 테그 정보
        :return: 추출된 텍스트
        """
        import bs4

        if tag is None:
            return ''

        if isinstance(tag, bs4.element.NavigableString) is True:
            return str(tag).strip()

        return tag.get_text().strip()

    def extract_image(self, soup, delete_caption=False):
        """
        기사 본문에서 이미지와 캡션 추출

        :param soup: HTML 파싱 개체
        :param delete_caption: 캡션 삭제 여부
        :return: 이미지 목록
        """

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
                        result.append({'image': tag['src'], 'caption': caption})
                    else:
                        next_element = None
                        result.append({'image': tag['src'], 'caption': ''})
                except Exception as e:
                    logging.error(msg='이미지 추출 에러: {}'.format(e))
            else:
                result.append({'image': tag['src'], 'caption': ''})

            # 캡션을 본문에서 삭제
            if delete_caption is True:
                try:
                    if next_element is not None:
                        next_element.replace_with('')

                    tag.replace_with('')
                except Exception as e:
                    logging.error(msg='이미지 캡션 추출 에러: {}'.format(e))

        return result

    def save_s3(self, document, s3_info, db_name):
        """ S3에 기사 이미지를 저장한다.

        :param document: 저장할 문서
        :param s3_info:
            s3 접속 정보::

                {
                    bucket: 'bucket name',
                    url: 'http://paige-cdn.plaync.com'
                }

        :param db_name: 디비명
        :return: document
        """
        import boto3
        import pathlib

        from bs4 import BeautifulSoup
        from botocore.exceptions import ClientError

        # 이미지 목록 추출
        image_list = None
        if 'image_list' in document:
            image_list = document['image_list']
        else:
            if 'html_content' in document:
                soup = BeautifulSoup(document['html_content'], 'lxml')
                image_list = self.extract_image(soup=soup)

        # 추출된 이미지 목록이 없을 경우
        if image_list is None:
            return

        # api 메뉴얼: http://boto3.readthedocs.io/en/latest/reference/services/s3.html
        bucket_name = s3_info['bucket']
        aws_access_key_id = os.getenv('S3_ACCESS_KEY', 'AKIAI5X5SF6WJK3SFXDA')
        aws_secret_access_key = os.getenv('S3_SECRET_ACCESS_KEY', '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')

        s3 = boto3.resource('s3',
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)

        bucket = s3.Bucket(bucket_name)

        # 이미지 목록
        count = 0
        prefix = document['_id']
        for image in image_list:
            url = image['image']

            # 이미지 확장자 추출
            suffix = pathlib.Path(url).suffix

            # 1. 이미지 파일 다운로드
            r = requests.get(url)

            upload_file = '{}/{}-{:02d}{}'.format(db_name, prefix, count, suffix)
            count += 1

            # 파일 확인
            file_exists = False
            try:
                s3.Object(bucket_name, upload_file).get()
                file_exists = True
            except ClientError as e:
                logging.info('{}'.format(e))

            if file_exists is True:
                # cdn 이미지 주소 추가
                image['cdn_image'] = '{}/{}'.format(s3_info['url_prefix'], upload_file)
                continue

            # 2. s3에 업로드
            try:
                response = bucket.put_object(Key=upload_file, Body=r.content, ACL='public-read',
                                             ContentType=r.headers['content-type'])
                logging.info(msg='save S3: {}'.format(response))

                # cdn 이미지 주소 추가
                image['cdn_image'] = '{}/{}'.format(s3_info['url_prefix'], upload_file)
            except Exception as e:
                logging.error(msg='s3 저장 오류: {}'.format(e))

        # 이미지 목록 업데이트
        document['image_list'] = image_list

        return document

    def get_elastic_index_info(self, db_name, elastic_info, article_date):
        """ elastic search 의 저장 정보

        :param db_name: 디비명
        :param elastic_info:
            elastic 접속 정보::

                {
                  "host": "http://nlpapi.ncsoft.com:9200",
                  "index": None,
                  "type": None,
                  "insert": true
                }

        :param article_date: 날짜
        :return: 인덱스, doc_type (날짜형: 2018-03)
        """
        # 인덱스 추출, 몽고 디비 collection 이름 우선

        index = db_name
        doc_type = None

        if 'index' in elastic_info and elastic_info['index'] != '' \
                and elastic_info['index'] != '{mongo.name}':
            index = elastic_info['index']

        if 'type' in elastic_info and elastic_info['type'] != '' \
                and elastic_info['type'] != '{mongo.collection}':
            doc_type = elastic_info['type']

        # date 에서 추출
        if doc_type is None:
            _, doc_type = self.get_date_collection_name(article_date)

        return index, doc_type

    def save_article_list(self, url, article_list, db_info):
        """ 기사 목록 저장

        :param url: url 주소
        :param article_list: 기사 목록
        :param db_info: 디비 접속 정보
        :return:
        """
        from dateutil.parser import parse as parse_date

        if 'db_name' in db_info:
            db_name = db_info['db_name']
        else:
            db_name = re.sub('^.+://(.+?)/', '\g<1>', url).replace('.', '_')

        # 날짜 추출
        date = datetime.now()
        if len(article_list) > 0 and 'datetime' in article_list[0]:
            try:
                date = parse_date(article_list[0]['datetime'])
            except Exception as e:
                logging.error(msg='{}'.format(e))

        # 저장할 문서 생성
        doc = {
            'url': url,
            'date': date,
            'article_list': article_list
        }

        # 저장
        if 'article_list' in db_info:
            batch_list = [db_info['article_list']]
            if isinstance(db_info['article_list'], list):
                batch_list = db_info['article_list']

            for elastic_info in batch_list:
                index = '{}_article_list'.format(db_name)

                if 'index' in elastic_info:
                    index = elastic_info['index']

                if 'host' not in elastic_info:
                    continue

                self.save_elastic(document=doc, db_name=index, insert=True, elastic_info=elastic_info)

        return

    def save_article(self, document, db_info):
        """ 문서 저장

        :param document: 저장할 문서
        :param db_info: 디비 접속 정보
        :return: True/False
        """
        import threading

        # 스래드로 작업 시작
        job = {
            'db_info': db_info,
            'document': document
        }

        # queue 목록에 작업 저장
        start_thread = False
        if self.job_queue.empty() is True:
            start_thread = True

            logging.info(msg='저장 큐에 저장: {:,}'.format(self.job_queue.qsize()))
            self.job_queue.put(job)

        if start_thread is True:
            # 스래드 시작
            thread = threading.Thread(target=self._save_article)
            thread.start()

        return True

    def _save_article(self):
        """ 스래드 안에서 문서 저장

        :return: True/False
        """
        if self.job_queue.empty() is True:
            return True

        logging.info(msg='크롤링 결과 저장: {:,}'.format(self.job_queue.qsize()))

        # 뮤텍스 구간
        if self.mutex is True:
            return False

        self.mutex = True

        while self.job_queue.empty() is False:
            # 작업 큐에서 작업을 가져온다.
            job = self.job_queue.get()

            db_info = job['db_info']
            document = job['document']

            # 디비명
            db_name = None
            if 'db_name' in db_info:
                db_name = db_info['db_name']

            update = False
            if 'update' in db_info:
                update = db_info['update']

            mongo_info = None
            if 'mongo' in db_info:
                mongo_info = db_info['mongo']

            # 문서 저장
            if 's3' in db_info and 'bucket' in db_info['s3']:
                document = self.save_s3(document=document, s3_info=db_info['s3'],
                                        db_name=db_name)

            if 'mongo' in db_info and 'host' in mongo_info:
                self.save_mongodb(document=document, mongodb_info=mongo_info,
                                  db_name=db_name, update=update)

            # if 'mqtt'in db_info and 'host' in db_info['mqtt']:
            #     self.send_mqtt_message(document=document, mqtt_info=db_info['kafka'])
            #
            # if 'kafka'in db_info and 'host' in db_info['kafka']:
            #     self.send_kafka_message(document=document, kafka_info=db_info['kafka'],
            #                             mongodb_info=mongo_info)
            #
            # if 'logs'in db_info and 'host' in db_info['logs']:
            #     self.save_logs(document=copy.deepcopy(document),
            #                    elastic_info=db_info['logs'], mongodb_info=mongo_info)

            # 엘라스틱 서치에 저장
            if 'elastic' in db_info:
                batch_list = [db_info['elastic']]
                if isinstance(db_info['elastic'], list):
                    batch_list = db_info['elastic']

                for elastic_info in batch_list:
                    if 'host' not in elastic_info:
                        continue

                    self.save_elastic(document=copy.deepcopy(document), elastic_info=elastic_info,
                                      db_name=db_name, insert=update)

            # 코퍼스 전처리 시작
            if 'corpus-process' in db_info:
                batch_list = [db_info['corpus-process']]
                if isinstance(db_info['corpus-process'], list):
                    batch_list = db_info['corpus-process']

                for api_info in batch_list:
                    if 'host' not in api_info:
                        continue

                    self.send_corpus_process(document=copy.deepcopy(document), api_info=api_info,
                                             db_name=db_name, update=update)

        self.mutex = False

        # 작업 큐가 빌때까지 반복
        self._save_article()

        return True

    def make_simple_url(self, document, parsing_info):
        """ url 단축

        :param document: 크롤링 문서
        :param parsing_info: 문서 파싱 정보: 단축 url 패턴 사용
        :return: True/False
        """
        try:
            query, base_url, parsed_url = self.get_query(document['url'])
        except Exception as e:
            logging.error(msg='make_simple_url: get_query 오류 {}'.format(e))
            return False

        if isinstance(document['url'], str):
            url_info = {
                'full': document['url'],
                'simple': '',
                'query': query
            }
        else:
            url_info = document['url']

        if 'url' in parsing_info:
            parsing_url = parsing_info['url']

            if 'source_url' in document:
                url_info['source'] = document['source_url']
                del document['source_url']

            try:
                if 'simple_query' in parsing_url:
                    str_query = parsing_url['simple_query'].format(**query)
                    url_info['simple'] = '{}?{}'.format(base_url, str_query)
            except Exception as e:
                logging.error(msg='simple_query 오류: {}'.format(e))

            simple_url = url_info['full']

            try:
                if 'replace' in parsing_url:
                    for pattern in parsing_url['replace']:
                        simple_url = re.sub(pattern['from'], pattern['to'], simple_url)

                    url_info['simple'] = simple_url
            except Exception as e:
                logging.error(msg='simple_query replace 오류: {}'.format(e))

        document['url'] = url_info

        # 문서 아이디 추출
        if 'id' in parsing_info:
            parsing_id = parsing_info['id']

            document_id = url_info['full']
            document_id = document_id.replace('{}://{}'.format(parsed_url.scheme, parsed_url.hostname), '')

            # url 에서 불용어 제거
            if 'replace' in parsing_id:
                try:
                    for pattern in parsing_id['replace']:
                        document_id = re.sub(pattern['from'], pattern['to'], document_id)

                    document['_id'] = document_id
                except Exception as e:
                    logging.error(msg='문서 아이디 추출 오류: {}'.format(e))

                    document['_id'] = self.get_document_id(document_id)
            else:
                document['_id'] = self.get_document_id(document_id)

            # id 패턴이 있다면 치환
            if '_id' in parsing_id:
                try:
                    key_exists = True
                    for k in re.findall(r'{([^}]+)}', parsing_id['_id']):
                        if k not in query:
                            key_exists = False
                            break

                    if key_exists is True and len(query) > 0:
                        document['_id'] = parsing_id['_id'].format(**query)
                except Exception as e:
                    logging.error(msg='문서 아이디 추출 오류: {}'.format(e))

                    document['_id'] = self.get_document_id(document_id)

        return True

    @staticmethod
    def get_next_id(collection, document_name='section_id', value='section'):
        """ auto-increment 기능 구현, 몽고 디비에 primary id 기능 구현

        :param collection: 컬랙션 이름
        :param document_name: 문서 아이디
        :param value: 헤더값
        :return: 마지막 값
        """
        query = {'_id': document_name}
        update = {'$inc': {value: 1}}

        cursor = collection.find_and_modify(query=query, update=update, new=True)

        default = {'_id': document_name, value: 0}
        if cursor is None:
            collection.insert_one(default)
            cursor = collection.find_and_modify(query=query, update=update, new=True)

        max_id = 0
        if cursor is None:
            collection.insert_one(default)
        else:
            max_id = cursor.get(value)
            if max_id > 1000000:
                collection.replace_one(query, default, upsert=True)

                max_id = 0

        return '{:06d}'.format(max_id)

    def save_section_info(self, document, mongodb_info, db_name, collection_name):
        """ 문서의 섹션 정보 저장

        :param document: 크롤링된 문서
        :param db_name: 디비명
        :param mongodb_info: 몽고 디비 접속 정보
        :param collection_name: 컬랙션 이름
        :return: True/False
        """
        if document is None or '_id' not in document or 'section' not in document:
            return False

        from pymongo import errors

        if 'name' in mongodb_info:
            db_name = mongodb_info['name']

        if db_name is None:
            return False

        # 디비 연결
        connect, mongodb = self.open_db(host=mongodb_info['host'],
                                        port=mongodb_info['port'],
                                        db_name=db_name)

        section_info = {
            '_id': '{}-{}'.format(document['_id'], document['section'])
        }

        for k in ['url', 'title', 'date', 'section', 'document_id']:
            if k in document:
                section_info[k] = document[k]

        # 몽고 디비에 문서 저장
        try:
            collection = mongodb.get_collection(collection_name)
            if 'update' in mongodb_info and mongodb_info['update'] is True:
                collection.replace_one({'_id': section_info['_id']}, section_info, upsert=True)
            else:
                collection.insert_one(section_info)
        except errors.DuplicateKeyError:
            # logging.error(msg='섹션 정보 저장 오류: 중복키')
            pass
        except Exception as e:
            logging.error(msg='섹션 정보 저장 오류: {}'.format(e))

            try:
                collection = mongodb.get_collection('error_{}'.format(collection_name))

                if '_id' in section_info:
                    collection.replace_one({'_id': section_info['_id']}, section_info, upsert=True)
                else:
                    collection.insert_one(section_info)
            except Exception as e:
                logging.error(msg='섹션 정보 저장 오류: {}'.format(e))

            return False

        # 디비 연결 해제
        connect.close()

        msg = [collection_name]
        for key in ['date', 'section', 'title', 'url']:
            if key in document and isinstance(document[key], str):
                msg.append(document[key])

        if len(msg) > 0:
            logging.info(msg='섹션 정보 저장:'.format('\t'.join(msg)))

        return True

    @staticmethod
    def get_value(data, key):
        """ 해쉬에서 해당 키의 값을 반환

        :param data: 해쉬
        :param key: 찾을 키
        :return: 값
        """
        if key in data:
            return data[key]

        return None

    @staticmethod
    def get_container_host_name(state):
        """ 컨테이너가 실행중인 서버 이름 반환

        :param state: 상태 정보
        :return: 컨테이너가 실행중인 서버 이름
        """
        host_name = os.getenv('CONTAINER_HOST_NAME', '')
        if host_name != '':
            state['host'] = host_name

        return host_name

    def update_state(self, str_state, current_date, job_info, scheduler_db_info, start_date, end_date):
        """ 현재 작업 상태 변경

        :param str_state:
            상태, running, ready, stop
            경과 시간
        :param current_date: 현재 날짜
        :param job_info: 작업 정보
        :param scheduler_db_info: scheduler 디비 접속 정보
        :param start_date: 시작 일자
        :param end_date: 종료 일자
        :return: True/False
        """
        state = job_info['state']

        # 컨테이너가 실행중인 서버 이름 등록
        self.get_container_host_name(state=state)

        # 상태 정보 갱신
        state['state'] = str_state
        if current_date is not None:
            total = end_date - start_date
            delta = current_date - start_date

            state['running'] = current_date.strftime('%Y-%m-%d')
            state['progress'] = '{:0.1f}'.format(delta.days / total.days * 100)
        elif str_state == 'done':
            state['progress'] = '100.0'
        else:
            state['running'] = ''

        job_info['state'] = state

        # 저장
        self.update_document(job_info, scheduler_db_info)

        return True

    @staticmethod
    def change_key(json_data, key_mapping):
        """ json 키를 변경

        :param json_data: json 데이터
        :param key_mapping: 키 매핑 정보
        :return: True/False
        """
        if key_mapping is None:
            return False

        for original in key_mapping:
            # 내부 설정용 값은 제외함
            if original[0] == '_':
                continue

            new_key = key_mapping[original]
            if original == new_key:
                continue

            if new_key != '' and original in json_data:
                json_data[new_key] = json_data[original]

        return True

    def get_query(self, url):
        """ url 에서 쿼리문을 반환

        :param url: url 주소
        :return: url 쿼리 파싱 결과 반환
        """
        from urllib.parse import urlparse, parse_qs

        url = self.get_url(url)

        url_info = urlparse(url)
        result = parse_qs(url_info.query)
        for key in result:
            result[key] = result[key][0]

        return result, '{}://{}{}'.format(url_info.scheme, url_info.netloc, url_info.path), url_info

    def update_state_by_id(self, str_state, job_info, scheduler_db_info, url, query_key_mapping=None):
        """ 현재 작업 상태 변경

        :param str_state: 경과 시간 (상태, running, ready, stoped)
        :param job_info: 작업 정보
        :param scheduler_db_info: scheduler 디비 접속 정보
        :param url: url 주소
        :param query_key_mapping: url 쿼리
        :return: True/False
        """
        # query 정보 추출
        query = {}
        if query_key_mapping is not None and url != '':
            query, _, _ = self.get_query(url)
            self.change_key(query, query_key_mapping)

        state = job_info['state']

        # 컨테이너가 실행중인 서버 이름 등록
        self.get_container_host_name(state=state)

        if 'year' in query:
            state['year'] = query['year']

        if 'start' in query:
            state['start'] = query['start']

        state['state'] = str_state

        if str_state == 'done':
            state['progress'] = '100.0'

        job_info['state'] = state

        # 저장
        self.update_document(job_info, scheduler_db_info)

        return True

    def update_document(self, document, db_info):
        """ 문서 저장

        :param document: 저장할 문서
        :param db_info: 디비 접속 정보
        :return: None
        """
        if db_info['file_db'] is True:
            return

        connect, db = self.open_db(db_info['name'],
                                   db_info['host'],
                                   db_info['port'])

        collection = db.get_collection(db_info['collection'])
        collection.replace_one({'_id': document['_id']}, document)

        connect.close()

        return

    def get_parsing_information(self, db_info, parsing_id):
        """ 디비에서 작업을 찾아 반환

        :param db_info: scheduler 디비 접속 정보
        :param parsing_id: 파싱 아이디
        :return: 섹션과 파싱 정보
        """
        if db_info['file_db'] is True:
            import json

            file_name = 'schedule/parsing/{}.json'.format(parsing_id)
            with open(file_name, 'r') as fp:
                body = ''.join(fp.readlines())
                parsing_info = json.loads(body)
        else:
            connect, db = self.open_db(db_info['name'],
                                       db_info['host'],
                                       db_info['port'])

            parsing_info = db.get_collection('parsing_information').find_one({'_id': parsing_id})

            connect.close()

        return parsing_info

    @staticmethod
    def get_meta_value(soup, result_list):
        """ 메타 테그 추출

        :param soup: html soup
        :param result_list: 메타 태그 결과
        :return: True/False
        """
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

        result_list.append({'meta': result})
        return True

    def get_target_value(self, soup, target_tag_info, result_list, base_url):
        """ 계층적으로 표현된 태그 정보를 따라가면서 값을 찾아냄.

        :param soup: HTML 파싱 개체
        :param target_tag_info: 찾을 테그 정보
        :param result_list: 찾은 값을 반환 결과
        :param base_url: 호출한 웹 주소
        :return: True/False
        """

        attribute = self.get_value(target_tag_info, 'attr')

        if attribute is None:
            tag_list = soup.findAll(target_tag_info['tag_name'])
        else:
            tag_list = soup.findAll(target_tag_info['tag_name'], attrs=attribute)

        for sub_soup in tag_list:
            if 'remove' in target_tag_info:
                attribute = self.get_value(target_tag_info['remove'], 'attr')
                self.replace_tag(sub_soup, [target_tag_info['remove']['tag_name']], '', attribute=attribute)

            if 'next_tag' in target_tag_info:
                self.get_target_value(sub_soup, target_tag_info['next_tag'], result_list, base_url)
            else:
                data = {}
                for key in target_tag_info['data']:
                    if key == 'replace':
                        continue

                    data_tag_info = target_tag_info['data'][key]

                    attribute = self.get_value(data_tag_info, 'attr')

                    if attribute is None:
                        data_tag = sub_soup.find(data_tag_info['tag_name'])
                    else:
                        data_tag = sub_soup.find(data_tag_info['tag_name'], attrs=attribute)

                    if 'remove' in data_tag_info:
                        self.replace_tag(data_tag, [data_tag_info['remove']['tag_name']], '',
                                         attribute=self.get_value(data_tag_info['remove'], 'attr'))

                    if data_tag is not None:
                        value_type = data_tag_info['value']

                        if data_tag.has_attr(value_type):
                            data[key] = data_tag[value_type]

                            if value_type in ['href', 'src']:
                                data[key] = urljoin(base_url, data[key])
                        elif value_type == 'text':
                            data[key] = data_tag.get_text().strip()
                        elif value_type == 'link_list':
                            # 관련 기사 목록과 같이 리스트 형태의 링크
                            if key not in data:
                                data[key] = []

                            for link in data_tag.find_all('a'):
                                if link.has_attr('href'):
                                    data[key].append(link['href'])
                        else:
                            # html
                            data[key] = str(data_tag.prettify())

                        # replace
                        if 'replace' in data_tag_info:
                            for pattern in data_tag_info['replace']:
                                data[key] = re.sub('\r?\n', ' ', data[key], flags=re.MULTILINE)
                                data[key] = re.sub(pattern['from'], pattern['to'], data[key], flags=re.DOTALL)

                if len(data) > 0:
                    result_list.append(data)

        return True

    @staticmethod
    def parse_date_string(date_string, is_end_date=False):
        """ 문자열 날짜 형식을 date 형으로 반환

        :param date_string: 2016-01, 2016-01-01
        :param is_end_date: 마지막 일자 플래그, 마지막 날짜의 경우
        :return: 변환된 datetime
        """
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        token = date_string.split('-')

        result = datetime.today()
        if len(token) == 2:
            result = datetime.strptime(date_string, '%Y-%m')

            if is_end_date is True:
                result += relativedelta(months=+1)
        elif len(token) == 3:
            result = datetime.strptime(date_string, '%Y-%m-%d')

            if is_end_date is True:
                result += relativedelta(days=+1)

        if is_end_date is True:
            result += relativedelta(microseconds=-1)

        return result

    @staticmethod
    def print_summary(start_time, total=0, count=0, tag=''):
        """ 크롤링 진행 상황을 출력한다.

        :param total: 전체 수량
        :param count: 현재 진행 수량
        :param start_time: 시작 시간
        :param tag:
        :return: True
        """
        from time import time
        from datetime import timedelta

        processing_time = round(time() - start_time)
        if total > 0:
            left_count = total - count

            processing_rate = count / total * 100

            speed = processing_time / count
            estimate = round(speed * left_count)

            if speed == 0:
                return False

            msg = '완료/남은수/전체/진행율/속도 = ({:,}/{:,}/{:,}/{:0.2f}%/{:0.2f}), ' \
                  '실행 시간 = {}, 남은 시간 = {}'.format(count, left_count, total, processing_rate, 1 / speed,
                                                  timedelta(seconds=processing_time), timedelta(seconds=estimate))
        else:
            msg = '실행 시간 = {}'.format(timedelta(seconds=processing_time))

        logging.info(msg='{} {}\n'.format(tag, msg))

        return True


if __name__ == '__main__':
    pass
