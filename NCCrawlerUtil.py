#!/usr/bin/env python3
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
import traceback

from time import sleep

from urllib.parse import urljoin
from pymongo import MongoClient
from datetime import datetime

from bs4 import BeautifulSoup, Comment

from pymongo import errors

from requests.packages.urllib3.exceptions import InsecureRequestWarning

from NCNlpUtil import NCNlpUtil

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(UserWarning)


class NCCrawlerUtil:
    """
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/39.0.2171.95 Safari/537.36'
        }
        self.job_info = None

        self.hostname = None
        self.request_count = 0

    @staticmethod
    def replace_tag(html_tag, tag_list, replacement='', attrs=None):
        """
        html 태그 중 특정 태그를 삭제
        ex) script, caption will be removed
        """
        if html_tag is None:
            return

        for tag_name in tag_list:
            for tag in html_tag.find_all(tag_name, attrs=attrs):
                if replacement == '':
                    tag.extract()
                else:
                    tag.replace_with(replacement)

        return

    @staticmethod
    def remove_comment(html_tag):
        """
        html 태그 중에서 주석 태그를 모두 제거
        """
        for element in html_tag(text=lambda text: isinstance(text, Comment)):
            element.extract()

        return

    @staticmethod
    def get_encoding_type(html_body):
        """
        메타 정보에서 인코딩 정보 반환
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
    def get_url(url):
        """
        url 문자열을 찾아서 반환
        """

        if isinstance(url, str) is True:
            return url
        elif 'simple' in url and url['simple'] != '':
            return url['simple']
        elif 'full' in url:
            return url['full']

        return ''

    def curl_html(self, curl_url, delay=6, min_delay=3,
                  post_data=None, json=False, encoding=None, max_try=3, headers=None):
        """
        랜덤하게 기다린후 웹 페이지 크롤링, 결과는 bs4 파싱 결과를 반환
        """
        curl_url = self.get_url(curl_url)
        curl_url = curl_url.strip()

        if curl_url == '' or curl_url.find('http') != 0:
            print('error empty url {}'.format(curl_url))
            return

        # 10번에 한번씩 10초간 쉬어줌
        self.request_count += 1
        if self.request_count % 10 == 0:
            delay = 10

        # 2초 이상일 경우 랜덤하게 쉬어줌
        sleep_time = delay
        if sleep_time > min_delay:
            sleep_time = random.randrange(min_delay, delay, 1)

        # 상태 출력
        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # NCNlpUtil().print('{}\t{} sec\t{:,}\t{}'.format(str_now, sleep_time, self.request_count, curl_url))

        # 쉼
        sleep(sleep_time)

        # 해더 생성
        if headers is None:
            headers = self.headers
        else:
            headers.update(self.headers)

        # 웹 크롤링
        try:
            if post_data is None:
                page_html = requests.get(curl_url, headers=headers, allow_redirects=True, timeout=60) #
            else:
                page_html = requests.post(curl_url, data=post_data, headers=self.headers, allow_redirects=True, timeout=60)
        except Exception as err:
            return None
            # if max_try > 0:
            #     NCNlpUtil().print(
            #         '{}\t{}\terror at requests\t{}\tsleep: {} sec\tmax try: {}'.format(
            #             str_now, curl_url, sys.exc_info()[0], sleep_time * 10, max_try))
            #     sleep(sleep_time * 10)
            #     return self.curl_html(
            #         curl_url=curl_url, delay=delay, min_delay=min_delay, post_data=post_data,
            #         json=json, encoding=encoding, max_try=max_try - 1)
            # else:
            #     print("Unexpected error:", sys.exc_info()[0], flush=True)
            #     raise

        # json 일 경우
        if json is True:
            try:
                return page_html.json()
            except Exception as err:
                if page_html.content == b'':
                    return None

                if max_try > 0:
                    NCNlpUtil().print(
                        '{}\t{}\terror at json\t{}\tsleep: {} sec'.format(
                            str_now, curl_url, sys.exc_info()[0], sleep_time * 10))
                    sleep(sleep_time * 10)
                    return self.curl_html(
                        curl_url=curl_url, delay=delay, min_delay=min_delay, post_data=post_data,
                        json=json, encoding=encoding, max_try=max_try - 1)
                else:
                    print('Unexpected error:', sys.exc_info()[0])
                    raise

        # post로 요청했을 때 바로 반환
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
        except Exception as err:
            pass

        return None

    def parse_html(self, article, soup, target_tags, article_list):
        """
        html 파싱, 지정된 태그에서 정보 추출
        """
        url = self.get_url(article['url'])

        for tag_info in target_tags:
            try:
                self.get_target_value(soup, tag_info, article_list, url)
            except Exception as err:
                NCNlpUtil().print({'ERROR': 'get target value', 'url': url})
                return None

        for item in article_list:
            for key in item:
                article[key] = item[key]

        return article

    @staticmethod
    def get_collection_name(date):
        """
        날짜와 컬랙션 이름 변환
        """
        import dateutil.parser

        collection = 'error'
        if isinstance(date, str) is True:
            try:
                date = dateutil.parser.parse(date)
                collection = date.strftime('%Y-%m')
            except Exception as err:
                NCNlpUtil().print({'ERROR': 'convert date', 'date': date})
                return None, collection
        elif isinstance(date, dict) is True:
            if 'date' in date:
                collection = '{}-{}'.format(date['year'], date['month'])

        return date, collection

    @staticmethod
    def open_db(db_name, host='gollum', port=27017):
        """
        몽고 디비 핸들 오픈
        """
        connect = MongoClient('mongodb://{}:{}'.format(host, port))
        db = connect.get_database(db_name)

        return connect, db

    @staticmethod
    def get_document_id(url):
        """
        url 주소를 문서 아이디로 반환
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

    def send_kafka_message(self, document, kafka_info, mongodb_info):
        """
        kafka 에 메세지 전송
        """
        if 'port' not in kafka_info:
            kafka_info['port'] = 9092

        try:
            from kafka import KafkaProducer

            producer = KafkaProducer(
                bootstrap_servers='{}:{}'.format(kafka_info['host'], kafka_info['port']), compression_type='gzip')

            # 크롤러 메타 정보 저장
            document['crawler_meta'] = kafka_info
            if self.job_info is not None:
                document['crawler_meta']['job_id'] = self.job_info['_id']

            document['crawler_meta']['collection'] = mongodb_info['collection']

            message = json.dumps(document, ensure_ascii=False, default=NCNlpUtil().json_serial)

            producer.send(kafka_info['topic'], bytes(message, encoding='utf-8')).get(timeout=5)
            producer.flush()
        except Exception as err:
            NCNlpUtil().print('ERROR at kafka: {}, {}'.format(kafka_info['topic'], sys.exc_info()[0]))

        return

    def send_mqtt_message(self, document, mqtt_info):
        """
        mqtt 에 메세지 전송
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
        except Exception as err:
            NCNlpUtil().print('ERROR at mqtt: {}'.format(sys.exc_info()[0]))

        return

    @staticmethod
    def create_elastic_index(elastic, index_name=None):
        """
        인덱스 생성
        """
        if elastic is None:
            return

        elastic.indices.create(
            index=index_name,
            body={
                'settings': {
                    'number_of_shards': 1,
                    'number_of_replicas': 0
                }
            }
        )

        return

    def insert_elastic(self, document, elastic_info, mongodb_info):
        """
        elastic search에 저장
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
            return

        # 날짜 변환
        if 'date' in document and isinstance(document['date'], datetime):
            document['date'] = document['date'].strftime('%Y-%m-%dT%H:%M:%S')

        # 입력시간 삽입
        document['insert_date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

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
            },{
                'doc': document,
                'doc_as_upsert': True
            }]

            elastic.bulk(index=elastic_info['index'], body=bulk_data, refresh=True)
        except Exception as err:
            traceback.print_exc(file=sys.stderr)

            print('ERROR at save elastic: {}'.format(sys.exc_info()[0]))

        return

    def save_mongodb(self, document, mongodb_info):
        """
        몽고 디비에 문서 저장
        """
        if document is None:
            return False

        if '_id' not in document:
            document['_id'] = self.get_document_id(document['url'])

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
        connect, mongodb = self.open_db(
            host=mongodb_info['host'],
            db_name=mongodb_info['name'],
            port=mongodb_info['port'])

        # 몽고 디비에 문서 저장
        try:
            collection = mongodb.get_collection(mongodb_info['collection'])

            if mongodb_info['upsert'] is True:
                collection.replace_one({'_id': document['_id']}, document, upsert=True)
            else:
                # del document['meta']
                collection.insert_one(document)
        except errors.DuplicateKeyError:
            print('DuplicateKeyError: {}, {}'.format(
                mongodb_info['collection'], document['_id']), file=sys.stderr, flush=True)
        except Exception as err:
            traceback.print_exc(file=sys.stderr)

            NCNlpUtil().print('ERROR at save: {}: {}'.format(sys.exc_info()[0], document))

            try:
                collection = mongodb.get_collection('error')

                if '_id' in document:
                    collection.replace_one({'_id': document['_id']}, document, upsert=True)
                else:
                    collection.insert_one(document)
            except Exception as err:
                pass

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
            NCNlpUtil().print('{}\t{}'.format(str_now, '\t'.join(msg)))

        return

    def save_logs(self, document, elastic_info, mongodb_info):
        """
        엘라스틱서치에 로그 저장
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
            return

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
        except Exception as err:
            traceback.print_exc(file=sys.stderr)

            print('ERROR at save elastic: {}'.format(sys.exc_info()[0]))

        return

    def save_article(self, document, db_info):
        """
        문서 저장
        """
        if 'mongo'in db_info and 'host' in db_info['mongo']:
            self.save_mongodb(document=document, mongodb_info=db_info['mongo'])

        if 'mqtt'in db_info and 'host' in db_info['mqtt']:
            self.send_mqtt_message(document=document, mqtt_info=db_info['kafka'])

        if 'kafka'in db_info and 'host' in db_info['kafka']:
            self.send_kafka_message(document=document, kafka_info=db_info['kafka'], mongodb_info=db_info['mongo'])

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
        """
        parsing_url = None
        if 'url' in parsing_info:
            parsing_url = parsing_info['url']

        if parsing_url is None:
            return

        query, base_url, parsed_url = self.get_query(document['url'])

        url_info = {
            'full': document['url'],
            'simple': '',
            'query': query
        }

        if 'source_url' in document:
            url_info['source'] = document['source_url']
            del document['source_url']

        if 'simple_query' in parsing_url:
            str_query = parsing_url['simple_query'].format(**query)
            url_info['simple'] = '{}?{}'.format(base_url, str_query)

        document['url'] = url_info

        # 문서 아이디 추출
        document_id = url_info['full']
        document_id = document_id.replace('{}://{}'.format(parsed_url.scheme, parsed_url.hostname), '')

        try:
            if '_id' in parsing_url:
                document['_id'] = parsing_url['_id'].format(**query)
            elif 'replace' in parsing_url:
                for pattern in parsing_url['replace']:
                    document_id = re.sub(pattern['from'], pattern['to'], document_id)

                document['_id'] = document_id
            else:
                document['_id'] = self.get_document_id(document_id)
        except Exception as err:
            document['_id'] = self.get_document_id(document_id)

        return

    @staticmethod
    def get_next_id(collection, document_name='section_id', value='section'):
        """
        auto-increment 기능 구현
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

        result = '{:06d}'.format(max_id)

        return result

    def save_section_info(self, document, mongodb_info, collection_name):
        """
        문서 저장
        """
        if document is None:
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

        except Exception as err:
            NCNlpUtil().print('ERROR at save: {}: {}'.format(sys.exc_info()[0], document))

            try:
                collection = mongodb.get_collection('error_{}'.format(collection_name))

                if '_id' in section_info:
                    collection.replace_one({'_id': section_info['_id']}, section_info, upsert=True)
                else:
                    collection.insert_one(section_info)
            except Exception as err:
                pass

            return False

        # 디비 연결 해제
        connect.close()

        msg = [collection_name]
        for key in ['date', 'section', 'title', 'url']:
            if key in document and isinstance(document[key], str):
                msg.append(document[key])

        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if len(msg) > 0:
            NCNlpUtil().print('{}\t{}'.format(str_now, '\t'.join(msg)))

        return True

    @staticmethod
    def get_value(data, key):
        if key in data:
            return data[key]

        return None

    @staticmethod
    def get_documents(db, collection_name):
        """
        디비에서 설정 정보를 모두 읽어옴
        """
        result = {}

        cursor = db[collection_name].find()
        cursor = cursor[:]
        for doc in cursor:
            doc_id = doc['_id']
            del doc['_id']

            result[doc_id] = doc

        return result

    def update_state(self, state, current_date, job_info, scheduler_db_info, start_date, end_date):
        """
        현재 작업 상태 변경
            # state: 상태, running, ready, stoped
            # status: 경과 시간
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
        return

    @staticmethod
    def change_key(json_data, key_mapping):
        """
        json 키를 변경
        """
        if key_mapping is None:
            return

        for original in key_mapping:
            # 내부 설정용 값은 제외함
            if original[0] == '_':
                continue

            new_key = key_mapping[original]
            if original == new_key:
                continue

            if new_key != '' and original in json_data:
                json_data[new_key] = json_data[original]

        return

    def get_query(self, url):
        """
        url 에서 쿼리문을 반환
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
            # state: 상태, running, ready, stoped
            # status: 경과 시간
        """
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
        return

    def get_parsing_information(self, scheduler_db_info):
        """
        디비에서 작업을 찾아 반환
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
        return

    def get_target_value(self, soup, target_tag_info, result_list, base_url):
        """
        계층적으로 표현된 태그 정보를 따라가면서 값을 찾아냄.
        """

        for sub_soup in soup.findAll(target_tag_info['tag_name'], attrs=self.get_value(target_tag_info, 'attr')):
            if 'remove' in target_tag_info:
                self.replace_tag(sub_soup, [target_tag_info['remove']['tag_name']], '',
                                 attrs=self.get_value(target_tag_info['remove'], 'attr'))

            if 'next_tag' in target_tag_info:
                self.get_target_value(sub_soup, target_tag_info['next_tag'], result_list, base_url)
            else:
                data = {}
                for key in target_tag_info['data']:
                    if key == 'replace':
                        continue

                    data_tag_info = target_tag_info['data'][key]

                    data_tag = sub_soup.find(
                        data_tag_info['tag_name'], attrs=self.get_value(data_tag_info, 'attr'))

                    if 'remove' in data_tag_info:
                        self.replace_tag(data_tag, [data_tag_info['remove']['tag_name']], '',
                                         attrs=self.get_value(data_tag_info['remove'], 'attr'))

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

        return

# end of NCCrawlerUtil


if __name__ == '__main__':
    pass

# end of __main__
