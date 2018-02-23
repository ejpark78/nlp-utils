#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import os
import sys
import copy
import json
import random
import requests
import logging
import urllib3
import traceback

from bs4 import BeautifulSoup, Comment
from time import sleep
from datetime import datetime
from urllib.parse import urljoin


class Utils(object):
    """
    크롤러 유틸
    """

    def __init__(self):
        super().__init__()

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        urllib3.disable_warnings(UserWarning)

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/62.0.3202.75 Safari/537.36'
        }

        self.job_info = None

        self.hostname = None
        self.request_count = 0

    @staticmethod
    def replace_tag(html_tag, tag_list, replacement='', attribute=None):
        """
        html 태그 중 특정 태그를 삭제
        ex) script, caption will be removed

        :param html_tag:
            html 본문

        :param tag_list:
            제거할 태그 목록

        :param replacement:
            치환할 문자

        :param attribute:
            특정 속성값 포함 여부

        :return:
            True/False
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
    def remove_comment(html_tag):
        """
        html 태그 중에서 주석 태그를 제거

        :param html_tag:
            웹페이지 본문

        :return:
            True/False
        """
        for element in html_tag(text=lambda text: isinstance(text, Comment)):
            element.extract()

        return True

    @staticmethod
    def get_encoding_type(html_body):
        """
        메타 정보에서 인코딩 정보 반환

        :param html_body:
            html 본문

        :return:
            BeautifulSoup 반환
        """
        soup = BeautifulSoup(html_body, 'lxml')

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
        """
        url 문자열을 찾아서 반환

        :param url:
            url 구조체

        :param url_type:
            url 타입 명시

        :return:
            url
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
                  encoding=None, max_try=3, headers=None):
        """
        랜덤하게 기다린후 웹 페이지 크롤링, 결과는 bs4 파싱 결과를 반환

        :param curl_url:
            받아올 URL 주소

        :param delay:
            delay 범위: 10~15, 10초에서 15초 사이

        :param post_data:
            post 방식으로 보낼때 data

        :param json_type:
            json 결과 형식 명시

        :param encoding:
            인코딩 명시

        :param max_try:
            최대 시도 횟수 명시

        :param headers:
            헤더 명시

        :return:
            크롤링 결과 반환, html or json 형식으로 반환
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
            print('error empty url {}'.format(curl_url))
            return

        # 2초 이상일 경우 랜덤하게 쉬어줌
        sleep_time = min_delay
        if sleep_time > max_delay:
            try:
                sleep_time = random.randrange(min_delay, max_delay, 1)
            except Exception as e:
                logging.error('', exc_info=e)

        # 10번에 한번씩 60초간 쉬어줌
        self.request_count += 1
        if self.request_count % 60 == 0:
            min_delay = 60
            max_delay = min_delay + 1

        # 상태 출력
        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 쉼
        print('{} curl_html sleep: {} secs'.format(str_now, sleep_time), flush=True)
        sleep(sleep_time)

        # 해더 생성
        if headers is None:
            headers = self.headers
        else:
            headers.update(self.headers)

        # 웹 크롤링
        try:
            if post_data is None:
                page_html = requests.get(url=curl_url, headers=headers, allow_redirects=True, timeout=60)
            else:
                page_html = requests.post(url=curl_url, data=post_data, headers=self.headers,
                                          allow_redirects=True, timeout=60)
        except Exception as e:
            logging.error('', exc_info=e)
            return None

        # json_type 일 경우
        if json_type is True:
            try:
                result = page_html.json()
            except Exception as e:
                logging.error('', exc_info=e)

                if page_html.content == b'':
                    return None

                if max_try > 0:
                    print(
                        '{}\t{}\terror at json\t{}\tsleep: {} sec'.format(
                            str_now, curl_url, sys.exc_info()[0], sleep_time * 10))
                    sleep(sleep_time * 10)
                    return self.curl_html(curl_url=curl_url, delay=delay, post_data=post_data,
                                          json_type=json_type, encoding=encoding, max_try=max_try - 1)
                else:
                    print('Unexpected error:', sys.exc_info()[0])
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
            if soup is not None and encoding is None:
                return soup

            return BeautifulSoup(content, 'lxml')
        except Exception as e:
            logging.error('', exc_info=e)

        return None

    def parse_html(self, article, soup, target_tags, article_list):
        """
        html 파싱, 지정된 태그에서 정보 추출

        :param article:
        :param soup:
        :param target_tags:
        :param article_list:
        :return:
        """
        url = self.get_url(article['url'])

        for tag_info in target_tags:
            try:
                self.get_target_value(soup, tag_info, article_list, url)
            except Exception as e:
                logging.error('', exc_info=e)
                print({'ERROR': 'get target value', 'url': url}, flush=True)
                return None

        for item in article_list:
            for key in item:
                article[key] = item[key]

        return article

    @staticmethod
    def get_date_collection_name(date):
        """
        날짜와 컬랙션 이름 변환

        :param date:
            날짜 문자열

        :return:
            날짜와 컬랙션 이름
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
                else:
                    date = parse_date(date)

                collection = date.strftime('%Y-%m')
            except Exception as e:
                logging.error('', exc_info=e)
                print({'ERROR': 'convert date', 'date': date}, flush=True)
                return None, collection
        elif isinstance(date, dict) is True:
            if 'date' in date:
                collection = '{}-{}'.format(date['year'], date['month'])

        return date, collection

    @staticmethod
    def open_db(db_name, host='gollum', port=27017):
        """
        몽고 디비 핸들 오픈

        :param db_name:
            데이터베이스명

        :param host:
            서버 주소

        :param port:
            서버 포트

        :return:
            접속 정보와 데이터베이스 핸들
        """
        from pymongo import MongoClient

        connect = MongoClient('mongodb://{}:{}'.format(host, port))
        db = connect.get_database(db_name)

        return connect, db

    @staticmethod
    def get_document_id(url):
        """
        url 주소를 문서 아이디로 반환

        :param url:
        :return:
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
        """
        json.dumps의 콜백 함수로 넘겨주는 함수
        날자 형식을 문자로 반환

        :param obj:
            dictionary

        :return:

        """
        # import pymongo
        from datetime import datetime

        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')

        raise TypeError("Type not serializable")

    def send_kafka_message(self, document, kafka_info, mongodb_info):
        """
        kafka 에 메세지 전송

        :param document:
            기사 본문

        :param kafka_info:
            카프카 접속 정보

            "kafka": {
              "host": "gollum",
              "result": {
                "elastic": {
                  "type": "2017-11",
                  "host": "frodo",
                  "index": "naver_society",
                  "upsert": true
                }
              },
              "job_id": "crawler_naver_society_2017",
              "port": 9092,
              "topic": "crawler"
            }

        :param mongodb_info:
            몽고 디비 정보: collection명 동기화

        :return:
            True/False

        콘솔에서 디버깅 방법
            $ kafka-topics.sh --list --zookeeper gollum:2181
            $ kafka-console-consumer.sh --bootstrap-server gollum:9092 --topic crawler --from-beginning

        """
        if 'port' not in kafka_info:
            kafka_info['port'] = 9092

        try:
            from kafka import KafkaProducer

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
            logging.error('', exc_info=e)

            print('ERROR at kafka: {}, {}'.format(kafka_info['topic'], sys.exc_info()[0]))

        return True

    def send_mqtt_message(self, document, mqtt_info):
        """
        mqtt로 메세지 전송

        :param document:
            기사 본문

        :param mqtt_info:
            mqtt 서버 접속 정보

        :return:
            True/False
        """
        import paho.mqtt.publish as publish

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
        # print('payload:', str_payload)

        try:
            if 'port' not in mqtt_info:
                mqtt_info['port'] = 1883

            publish.single(
                topic=mqtt_info['topic'],
                payload=str_payload, qos=2,
                hostname=mqtt_info['host'], port=mqtt_info['port'],
                client_id='')
        except Exception as e:
            logging.error('', exc_info=e)
            print('ERROR at mqtt: {}'.format(sys.exc_info()[0]))

        return True

    @staticmethod
    def create_elastic_index(elastic, index_name=None):
        """
        elasticsearch 인덱스 생성

        :param elastic:
            elastic 서버 접속 정보

        :param index_name:
            생성할 인덱스 이름

        :return:
            True/False
        """
        if elastic is None:
            return False

        elastic.indices.create(
            index=index_name,
            body={
                'settings': {
                    'number_of_shards': 3,
                    'number_of_replicas': 2
                }
            }
        )

        return True

    def insert_elastic(self, document, elastic_info, mongodb_info):
        """
        elastic search 에 문서 저장

        :param document:
            문서

        :param elastic_info:
            elastic 접속 정보

            "elastic": {
              "upsert": true,
              "index": "daum_economy",
              "type": "",
              "host": "http://nlpapi.ncsoft.com:9200"
            }

        :param mongodb_info:
            몽고디비 접속 정보, collection 이름 동기화

        :return:
            True/False
        """
        from elasticsearch import Elasticsearch

        # 인덱스 추출, 몽고 디비 collection 이름 우선
        if 'index' not in elastic_info:
            elastic_info['index'] = ''

        index = elastic_info['index']
        if 'name' in mongodb_info:
            index = mongodb_info['name']

        # 타입 추출, 몽고 디비 collection 이름 우선
        if 'type' not in elastic_info:
            elastic_info['type'] = ''

        index_type = elastic_info['type']
        if 'collection' in mongodb_info:
            index_type = mongodb_info['collection']

        if index == '' or index_type == '':
            return False

        # 날짜 변환
        if 'date' in document and isinstance(document['date'], datetime):
            document['date'] = document['date'].strftime('%Y-%m-%dT%H:%M:%S')

        # 입력시간 삽입
        document['insert_date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        try:
            # if 'auth' in elastic_info and elastic_info['auth'] is not None:
            #     elastic = Elasticsearch(
            #         [elastic_info['host']],
            #         http_auth=elastic_info['auth'],
            #         use_ssl=True,
            #         verify_certs=False,
            #         port=9200)
            # else:
            #     elastic = Elasticsearch(
            #         [elastic_info['host']],
            #         use_ssl=True,
            #         verify_certs=False,
            #         port=9200)

            elastic = Elasticsearch(hosts=[elastic_info['host']], timeout=30)

            if elastic.indices.exists(index) is False:
                self.create_elastic_index(elastic, index)

            document['document_id'] = document['_id']
            del document['_id']

            bulk_data = [{
                'update': {
                    '_index': index,
                    '_type': index_type,
                    '_id': document['document_id']
                }
            }, {
                'doc': document,
                'doc_as_upsert': True
            }]

            elastic.bulk(index=elastic_info['index'], body=bulk_data, refresh=True)
        except Exception as e:
            logging.error('', exc_info=e)
            traceback.print_exc(file=sys.stderr)

            print('ERROR at save elastic: {}'.format(sys.exc_info()[0]))

        return True

    def save_mongodb(self, document, mongodb_info):
        """
        몽고 디비에 문서 저장

        :param document:
            저장할 문서

        :param mongodb_info:
            몽고 디비 접속 정보

        "mongo": {
            "collection": "2017-07",
            "port": 27018,
            "upsert": false,
            "host": "frodo",
            "name": "daum_economy"
        }

        :return:
            True/False
        """
        from pymongo import errors

        if document is None:
            return False

        if '_id' not in document:
            url = self.get_url(document['url'])
            document['_id'] = self.get_document_id(url)

        if 'port' not in mongodb_info:
            mongodb_info['port'] = 27017

        if 'collection' not in mongodb_info:
            mongodb_info['collection'] = None

        meta = {}
        if 'meta' in document:
            for k in document['meta']:
                if k.find('.') >= 0:
                    meta[k.replace('.', '_')] = document['meta'][k]
                    continue

                meta[k] = document['meta'][k]

            document['meta'] = meta

        # 디비 연결
        connect, mongodb = self.open_db(host=mongodb_info['host'], db_name=mongodb_info['name'],
                                        port=mongodb_info['port'])

        # 몽고 디비에 문서 저장
        try:
            collection = mongodb.get_collection(mongodb_info['collection'])

            # upsert 모드인 경우 문서를 새로 저장
            if mongodb_info['upsert'] is True:
                collection.replace_one({'_id': document['_id']}, document, upsert=True)
            else:
                collection.insert_one(document)
        except errors.DuplicateKeyError:
            print('DuplicateKeyError: {}, {}'.format(mongodb_info['collection'], document['_id']),
                  file=sys.stderr, flush=True)
        except Exception as e:
            logging.error('', exc_info=e)
            traceback.print_exc(file=sys.stderr)
            print('ERROR at save: {}: {}'.format(sys.exc_info()[0], document), file=sys.stderr, flush=True)

            # 저장에 실패할 경우 error 컬랙션에 저장
            try:
                collection = mongodb.get_collection('error')

                if '_id' in document:
                    collection.replace_one({'_id': document['_id']}, document, upsert=True)
                else:
                    collection.insert_one(document)
            except Exception as e:
                logging.error('', exc_info=e)

            return False

        # 연결 종료
        connect.close()

        # 섹션 정보 저장
        if 'section' in document:
            self.save_section_info(
                document=document, mongodb_info=mongodb_info,
                collection_name='section_{}'.format(mongodb_info['collection']))

        # 현재 상황 출력
        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        msg = [mongodb_info['host'], mongodb_info['name'], mongodb_info['collection']]
        for key in ['_id', 'date', 'section', 'title', 'url']:
            if key in document and isinstance(document[key], str):
                msg.append(document[key])

        if len(msg) > 0:
            print('{}\t{}'.format(str_now, '\t'.join(msg)))

        return True

    def save_logs(self, document, elastic_info, mongodb_info):
        """
        엘라스틱서치에 로그 저장

        :param document:
            크롤링 결과 문서

        :param elastic_info:
            elastic 접속 정보

        :param mongodb_info:
            몽고 디비 접속 정보: collection 이름 사용

        :return:
            True/False
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

        try:
            if 'auth' in elastic_info and elastic_info['auth'] is not None:
                elastic = Elasticsearch(
                    [elastic_info['host']],
                    http_auth=elastic_info['auth'],
                    use_ssl=True,
                    verify_certs=False,
                    port=9200)
            else:
                elastic = Elasticsearch(
                    [elastic_info['host']],
                    use_ssl=True,
                    verify_certs=False,
                    port=9200)

            if elastic.indices.exists(elastic_info['index']) is False:
                self.create_elastic_index(elastic, elastic_info['index'])

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

            elastic.bulk(index=elastic_info['index'], body=bulk_data, refresh=True)
        except Exception as e:
            logging.error('', exc_info=e)
            traceback.print_exc(file=sys.stderr)

            print('ERROR at save elastic: {}'.format(sys.exc_info()[0]))

        return True

    def save_article(self, document, db_info):
        """
        문서 저장

        :param document:
            저장할 문서

        :param db_info:
            디비 접속 정보

        :return:
            True/False
        """
        if 'mongo'in db_info and 'host' in db_info['mongo']:
            self.save_mongodb(document=document, mongodb_info=db_info['mongo'])

        if 'mqtt'in db_info and 'host' in db_info['mqtt']:
            self.send_mqtt_message(document=document, mqtt_info=db_info['kafka'])

        # if 'kafka'in db_info and 'host' in db_info['kafka']:
        #     self.send_kafka_message(document=document, kafka_info=db_info['kafka'], mongodb_info=db_info['mongo'])

        # 엘라스틱 서치에 저장
        if 'elastic'in db_info and 'host' in db_info['elastic']:
            self.insert_elastic(
                document=copy.deepcopy(document), elastic_info=db_info['elastic'], mongodb_info=db_info['mongo'])

        if 'logs'in db_info and 'host' in db_info['logs']:
            self.save_logs(
                document=copy.deepcopy(document), elastic_info=db_info['logs'], mongodb_info=db_info['mongo'])

        return True

    def make_simple_url(self, document, parsing_info):
        """
        url 단축

        :param document:
            크롤링 문서

        :param parsing_info:
            문서 파싱 정보: 단축 url 패턴 사용

        :return:
            True/False
        """
        try:
            query, base_url, parsed_url = self.get_query(document['url'])
        except Exception as e:
            print(e, document, flush=True)
            return False

        url_info = {
            'full': document['url'],
            'simple': '',
            'query': query
        }

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
                logging.error('', exc_info=e)

            simple_url = url_info['full']

            try:
                if 'replace' in parsing_url:
                    for pattern in parsing_url['replace']:
                        simple_url = re.sub(pattern['from'], pattern['to'], simple_url)

                    url_info['simple'] = simple_url
            except Exception as e:
                logging.error('', exc_info=e)

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
                    logging.error('', exc_info=e)
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
                    logging.error('', exc_info=e)
                    document['_id'] = self.get_document_id(document_id)

        return True

    @staticmethod
    def get_next_id(collection, document_name='section_id', value='section'):
        """
        auto-increment 기능 구현
        몽고 디비에 primary id 기능 구현

        :param collection:
            컬랙션 이름

        :param document_name:
            문서 아이디

        :param value:

        :return:
            마지막 값
        """
        cursor = collection.find_and_modify(query={'_id': document_name}, update={'$inc': {value: 1}}, new=True)

        if cursor is None:
            collection.insert_one({'_id': document_name, value: 0})
            cursor = collection.find_and_modify(query={'_id': document_name}, update={'$inc': {value: 1}}, new=True)

        max_id = 0
        if cursor is None:
            collection.insert_one({'_id': document_name, value: 0})
        else:
            max_id = cursor.get(value)
            if max_id > 1000000:
                collection.replace_one(
                    {'_id': document_name},
                    {'_id': document_name, value: 0},
                    upsert=True)

                max_id = 0

        return '{:06d}'.format(max_id)

    def save_section_info(self, document, mongodb_info, collection_name):
        """
        문서의 섹션 정보 저장

        :param document:
            크롤링된 문서

        :param mongodb_info:
            몽고 디비 접속 정보

        :param collection_name:
            컬랙션 이름

        :return:
            True/False
        """
        if document is None or '_id' not in document or 'section' not in document:
            return False

        from pymongo import errors

        # 디비 연결
        connect, mongodb = self.open_db(
            host=mongodb_info['host'],
            db_name=mongodb_info['name'],
            port=mongodb_info['port'])

        section_info = {
            '_id': '{}-{}'.format(document['_id'], document['section'])
        }

        for k in ['url', 'title', 'date', 'section', 'document_id']:
            if k in document:
                section_info[k] = document[k]

        # 몽고 디비에 문서 저장
        try:
            collection = mongodb.get_collection(collection_name)
            if mongodb_info['upsert'] is True:
                collection.replace_one({'_id': section_info['_id']}, section_info, upsert=True)
            else:
                collection.insert_one(section_info)
        except errors.DuplicateKeyError:
            pass
        except Exception as e:
            logging.error('', exc_info=e)
            print('ERROR at save: {}: {}'.format(sys.exc_info()[0], document))

            try:
                collection = mongodb.get_collection('error_{}'.format(collection_name))

                if '_id' in section_info:
                    collection.replace_one({'_id': section_info['_id']}, section_info, upsert=True)
                else:
                    collection.insert_one(section_info)

            except Exception as e:
                logging.error('', exc_info=e)

            return False

        # 디비 연결 해제
        connect.close()

        msg = [collection_name]
        for key in ['date', 'section', 'title', 'url']:
            if key in document and isinstance(document[key], str):
                msg.append(document[key])

        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if len(msg) > 0:
            print('{}\t{}'.format(str_now, '\t'.join(msg)))

        return True

    @staticmethod
    def get_value(data, key):
        """
        해쉬에서 해당 키의 값을 반환

        :param data:
            해쉬

        :param key:
            찾을 키

        :return:
            값
        """
        if key in data:
            return data[key]

        return None

    @staticmethod
    def get_documents(db, collection_name):
        """
        디비에서 설정 정보를 모두 읽어옴

        :param db:
            몽고 디비 데이터 베이스 핸들

        :param collection_name:
            컬랙션 이름

        :return:
            결과 문서
        """
        result = {}

        cursor = db.get_collection(collection_name).find({})
        cursor = cursor[:]
        for doc in cursor:
            doc_id = doc['_id']
            del doc['_id']

            result[doc_id] = doc

        return result

    def update_state(self, state, current_date, job_info, scheduler_db_info, start_date, end_date):
        """
        현재 작업 상태 변경

        :param state:
            상태, running, ready, stop
            경과 시간

        :param current_date:
            현재 날짜

        :param job_info:
            작업 정보

        :param scheduler_db_info:
            scheduler 디비 접속 정보

        :param start_date:
            시작 일자

        :param end_date:
            종료 일자

        :return:
            True/False
        """
        job_info['state']['state'] = state
        if current_date is not None:
            total = end_date - start_date
            delta = current_date - start_date

            job_info['state']['running'] = current_date.strftime('%Y-%m-%d')
            job_info['state']['progress'] = '{:0.1f}'.format(delta.days / total.days * 100)
        elif state == 'done':
            job_info['state']['progress'] = '100.0'

        connect, db = self.open_db(
            scheduler_db_info['scheduler_db_name'],
            scheduler_db_info['scheduler_db_host'],
            scheduler_db_info['scheduler_db_port'])

        collection_name = scheduler_db_info['scheduler_db_collection']
        db[collection_name].replace_one({'_id': job_info['_id']}, job_info)

        connect.close()

        return True

    @staticmethod
    def change_key(json_data, key_mapping):
        """
        json 키를 변경

        :param json_data:
            json 데이터

        :param key_mapping:
            키 매핑 정보

        :return:
            True/False
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
        """
        url 에서 쿼리문을 반환

        :param url:
            url 주소

        :return:
            url 쿼리 파싱 결과 반환
        """
        from urllib.parse import urlparse, parse_qs

        url = self.get_url(url)

        url_info = urlparse(url)
        result = parse_qs(url_info.query)
        for key in result:
            result[key] = result[key][0]

        return result, '{}://{}{}'.format(url_info.scheme, url_info.netloc, url_info.path), url_info

    def update_state_by_id(self, state, job_info, scheduler_db_info, url, query_key_mapping=None):
        """
        현재 작업 상태 변경

        :param state:
            상태, running, ready, stoped
            경과 시간

        :param job_info:
            작업 정보

        :param scheduler_db_info:
            scheduler 디비 접속 정보

        :param url:
            url 주소

        :param query_key_mapping:
            url 쿼리

        :return:
            True/False
        """
        if query_key_mapping is None:
            return False

        query, _, _ = self.get_query(url)
        self.change_key(query, query_key_mapping)

        if 'year' in query:
            job_info['state']['year'] = query['year']

        if 'start' in query:
            job_info['state']['start'] = query['start']

        job_info['state']['state'] = state

        if state == 'done':
            job_info['state']['progress'] = '100.0'

        connect, db = self.open_db(
            scheduler_db_info['scheduler_db_name'],
            scheduler_db_info['scheduler_db_host'],
            scheduler_db_info['scheduler_db_port'])

        collection = db.get_collection(scheduler_db_info['scheduler_db_collection'])
        collection.replace_one({'_id': job_info['_id']}, job_info)

        connect.close()

        return True

    def get_parsing_information(self, scheduler_db_info):
        """
        디비에서 작업을 찾아 반환

        :param scheduler_db_info:
            scheduler 디비 접속 정보

        :return:
            섹션과 파싱 정보
        """
        connect, db = self.open_db(
            scheduler_db_info['scheduler_db_name'],
            scheduler_db_info['scheduler_db_host'],
            scheduler_db_info['scheduler_db_port'])

        section_info = self.get_documents(db, 'section_information')
        parsing_info = self.get_documents(db, 'parsing_information')

        connect.close()

        return section_info, parsing_info

    @staticmethod
    def get_meta_value(soup, result_list):
        """
        메타 테그 추출

        :param soup:
            html soup

        :param result_list:
            메타 태그 결과

        :return:
            True/False
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
        """
        계층적으로 표현된 태그 정보를 따라가면서 값을 찾아냄.

        :param soup:
        :param target_tag_info:
        :param result_list:
        :param base_url:
        :return:
            True/False
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
                            data[key] = str(data_tag)

                        # replace
                        if 'replace' in data_tag_info:
                            for pattern in data_tag_info['replace']:
                                # data[key] = re.sub(pattern['from'], pattern['to'], data[key], re.DOTALL)
                                data[key] = re.sub('\r?\n', ' ', data[key], flags=re.MULTILINE)
                                data[key] = re.sub(pattern['from'], pattern['to'], data[key], flags=re.DOTALL)

                if len(data) > 0:
                    result_list.append(data)

        return True

    def news2csv(self):
        """
        몽고디비의 뉴스를 csv 형태로 추출

        :return:
            True/False
        """
        from language_utils.language_utils import LanguageUtils

        util = LanguageUtils()

        fp_csv = {}

        total_count = {
            'document': 0,
            'sentence': 0,
            'token': 0
        }

        for line in sys.stdin:
            document = json.loads(line)
            document = util._get_text(document)

            if 'paragraph' not in document or len(document['paragraph']) == 0:
                continue

            if 'date' not in document:
                continue

            paragraph = document['paragraph']

            document['url'] = document['url']['full']
            document['date'] = document['date']['$date'].replace('T', ' ').replace('Z', '').replace('.000', '')

            # 제목 헤더 추출
            header, document['title'] = self._split_news_header(sentence=document['title'])
            if 'title_header' not in document or document['title_header'] == '':
                document['title_header'] = header

            # 분문 헤더 추출
            header, paragraph[0][0] = self._split_news_header(sentence=paragraph[0][0])
            if 'source' not in document or document['source'] == '':
                document['source'] = header

            buf = []
            count = 0
            sentence_token = 0
            for i in range(len(paragraph)):
                for j in range(len(paragraph[i])):
                    one_line = paragraph[i][j].strip()

                    if one_line == '':
                        continue

                    sentence_list = [one_line]
                    if one_line.find('"') >= 0:
                        sentence_list = []
                        for qoute in re.findall(r'"([^"]{10,1024})"', one_line):
                            sentence_list += util.split_sentence(qoute)

                    for sentence in sentence_list:
                        if sentence == '':
                            continue

                        email = re.findall(r'([a-zA-Z.-]+@[a-zA-Z-]+\.[a-zA-Z-]+)', sentence)
                        if len(email) > 0:
                            continue

                        col = []
                        for k in ['_id', 'url', 'section', 'date', 'source', 'title_header', 'title']:
                            if k in document:
                                col.append(document[k])
                            else:
                                col.append('')

                        col.append(str(i+1))
                        col.append(str(j+1))
                        col.append(sentence)

                        count += 1
                        sentence_token += sentence.count(' ') + 1

                        buf.append('\t'.join(col))

            if count == 0:
                continue

            total_count['document'] += 1
            total_count['sentence'] += count
            total_count['token'] += sentence_token

            # 문장수 10 ~ 15 문장만 저장
            if count < 10 or count > 15:
                continue

            # 평균 어절수 5 ~ 20 문장만 저장
            avg_token = int(sentence_token / count)
            if avg_token < 5 or avg_token > 20:
                continue

            f_tag = 'count({:02d})/token({:02d})/[{}].[{}].[{}]'.format(
                count,
                avg_token,
                document['section'],
                document['source'],
                document['title_header']
            )

            if f_tag not in fp_csv:
                if len(fp_csv) > 500:
                    for f_tag in fp_csv:
                        fp_csv[f_tag].flush()
                        fp_csv[f_tag].close()

                    fp_csv = {}

                fname = 'data/nate_baseball/csv/{}.csv'.format(f_tag)
                fpath = os.path.dirname(fname)
                if os.path.exists(fpath) is not True:
                    os.makedirs(fpath)

                fp_csv[f_tag] = open(fname, 'a')

            fp_csv[f_tag].write('\n'.join(buf) + '\n\n')
            fp_csv[f_tag].flush()
            print(f_tag)

        for f_tag in fp_csv:
            fp_csv[f_tag].close()

        # if fp is not None:
        #     fp.close()

        print('\n문서수: {:,}\n문장수: {:,}\n어절수: {:,}\n'
              '문서별 평균 문장수: {:0.2f}\n문서별 평균 어절 수: {:0.2f}\n문장별 평균 어절 수: {:0.2f}'.format(
                total_count['document'],
                total_count['sentence'],
                total_count['token'],
                total_count['sentence']/total_count['document'],
                total_count['token'] / total_count['document'],
                total_count['token'] / total_count['sentence']
        ))

        return True

    @staticmethod
    def _split_news_header(sentence):
        """
        뉴스 문장에서 헤더 추출

        [포토]한화 한용덕 감독, 임기내 우승권 팀 만들어야
        [사진]김태균,'한용덕 감독님! 우승 한번 시켜주십시오'

        :return:
            헤더 정보
        """

        header = ''
        try:
            for str_p in [r'^\s*\[([^]]+)\]\s*', r'^\s*\(([^)]+)\)\s*']:
                p = re.compile(str_p)
                m = re.findall(p, sentence)
                if len(m) > 0:
                    header = m[0].split('=', maxsplit=1)[0]
                    sentence = re.sub(p, '', sentence)
        except Exception as e:
            logging.error('', exc_info=e)

        return header, sentence

    @staticmethod
    def csv2ellipsis():
        """

        :return:
        """

        # 20170425n44151
        # http://sports.news.nate.com/view/20170425n44151
        # 해외야구
        # 2017-04-25 22:02:00
        # 서울
        # 프로야구
        # 넥센의 무서운 화력, 두산 상대로 선발 전원 안타·득점
        # 9
        # 2
        # 허정엽 역시 장타 능력을 과시하며 4타수 1안타 4타점을 기록했다.

        """

find . -name "*화보*" -exec rm {} \;
find . -name "*포토*" -exec rm {} \;
find . -name "*[KS]*" -exec rm {} \;
find . -name "*[PO]*" -exec rm {} \;
find . -name "*S-girl*" -exec rm {} \;



time bzcat data/nate_baseball/2017-04.json.bz2 \
    data/nate_baseball/2017-05.json.bz2 \
    data/nate_baseball/2017-06.json.bz2 \
    data/nate_baseball/2017-07.json.bz2 \
    data/nate_baseball/2017-08.json.bz2 \
    data/nate_baseball/2017-09.json.bz2 \
    data/nate_baseball/2017-10.json.bz2 \
    | ./batch.py

        
        
{
    "session": "1",
    "memo": "",
    "meta": {
        "id": "20170425n44151",
        "url": "http://sports.news.nate.com/view/20170425n44151",
        "date": "2017-04-25 22:02:00",
        "title": "넥센의 무서운 화력, 두산 상대로 선발 전원 안타·득점",
        "section": "",
    },
    "sentence_list": [
        {
            "sentence": "허정엽 역시 장타 능력을 과시하며 4타수 1안타 4타점을 기록했다.",
            "id": "1",
            "user": "A"
        },
        (...)
    ]
}        


        col = []
        for k in ['_id', 'url', 'section', 'date', 'source', 'title_header', 'title']:
            if k in document:
                col.append(document[k])
            else:
                col.append('')

        col.append(str(i+1))
        col.append(str(j+1))
        col.append(sentence)

        """

        total_count = {
            'document': 0,
            'sentence': 0,
            'token': 0
        }

        count = 0
        session = 1

        buf = {
            'sentence_list': []
        }

        prev_id = ''
        for line in sys.stdin:
            line = line.strip()
            if line == '':
                continue

            token = line.split('\t')

            if prev_id != '' and token[0] != prev_id:
                fname = 'data/nate_baseball/work/C{:03d}/{:05d}.json'.format(int(session / 100), session)

                fpath = os.path.dirname(fname)
                if os.path.exists(fpath) is not True:
                    os.makedirs(fpath)

                with open(fname, 'w') as fp:
                    result = json.dumps(buf, ensure_ascii=False, indent=4, sort_keys=True)
                    fp.write(result + '\n')
                    fp.flush()

                    total_count['document'] += 1

                with open('{}/file-state.json'.format(fpath), 'a') as fp:
                    result = json.dumps({
                        'filename': '{:05d}.json'.format(session),
                        'state': {}
                    })

                    fp.write(result + '\n')
                    fp.flush()

                session += 1
                buf = {
                    'sentence_list': []
                }

            buf['session'] = session
            buf['memo'] = ''
            buf['meta'] = {
                'id': token[0],
                'url': token[1],
                'section': token[2],
                'date': token[3],
                'title': token[6]
            }

            item = {
                'sentence': token[9],
                'id': count,
                'user': '{:03d}'.format(len(buf['sentence_list']) + 1)
            }

            buf['sentence_list'].append(item)

            total_count['token'] += token[9].count(' ') + 1

            count += 1
            prev_id = token[0]

        total_count['sentence'] = count

        print('\n문서수: {:,}\n문장수: {:,}\n어절수: {:,}\n'
              '문서별 평균 문장수: {:0.2f}\n문서별 평균 어절 수: {:0.2f}\n문장별 평균 어절 수: {:0.2f}'.format(
                total_count['document'],
                total_count['sentence'],
                total_count['token'],
                total_count['sentence']/total_count['document'],
                total_count['token'] / total_count['document'],
                total_count['token'] / total_count['sentence']
                ))

        return

    @staticmethod
    def news2text():
        """
        문장 분리 적용 후 기사별 저장

        :return:
            True/False

        :sample extraction:
            $ bzcat 2017-10.json.bz2 | shuf | shuf | head -n100 | bzip2 - > 2017-10.sample.json.bz2
        """
        import bz2
        from crawler.html_parser import HtmlParser

        html_parser = HtmlParser()

        fp = bz2.open('data/nate_baseball/raw/2017-10.sample.json.bz2', 'r')

        count = 0
        for line in fp.readlines():
            line = str(line, encoding='utf-8')

            document = json.loads(line)
            if 'html_content' not in document:
                continue

            content, _ = html_parser.get_article_body(document['html_content'])

            content = content.strip()
            content = re.sub(r'\n+', '\n', content)
            content = content.replace('.', './/')
            content = content.replace(']', ']//')
            content = content.replace('= ', '= //')

            # 2017.//10.//13
            # jhno@sportschosun.//com, kphoto@mydaily.//co.//kr

            count += content.count('\n') + 1

            f_tag = '{}'.format(document['_id'])

            fname = 'data/nate_baseball/text/{}.json'.format(f_tag)
            fpath = os.path.dirname(fname)
            if os.path.exists(fpath) is not True:
                os.makedirs(fpath)

            with open(fname, 'w') as fp_out:
                result = {
                    'id': document['_id'],
                    'url': document['url']['full'],
                    'content': content
                }
                msg = json.dumps(result, ensure_ascii=False, indent=4, sort_keys=True)

                fp_out.write('{}\n'.format(msg))
                fp_out.flush()

        if fp is not None:
            fp.close()

        print('{:,}'.format(count))

        return True

    @staticmethod
    def parse_date_string(date_string, is_end_date=False):
        """
        문자열 날짜 형식을 date 형으로 반환

        :param date_string:
            2016-01, 2016-01-01

        :param is_end_date:
            마지막 일자 플래그, 마지막 날짜의 경우

        :return:
            변환된 datetime
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
        """
        크롤링 진행 상황을 출력한다.
        :param total:
            전체 수량

        :param count:
            현재 진행 수량

        :param start_time:
            시작 시간

        :param tag:

        :return:
            True
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
                  '실행 시간 = {}, 남은 시간 = {}'.format(count, left_count, total, processing_rate, 1/speed,
                                                  timedelta(seconds=processing_time), timedelta(seconds=estimate))
        else:
            msg = '실행 시간 = {}'.format(timedelta(seconds=processing_time))

        print('{} {}\n'.format(tag, msg), file=sys.stderr, flush=True)

        return True


if __name__ == '__main__':
    pass
