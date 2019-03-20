#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
import os
import pathlib
import pickle
import queue
import threading
from datetime import datetime

import requests

from module.html_parser import HtmlParser
from module.logging_format import LogMessage as LogMsg

MESSAGE = 25

logger = logging.getLogger()


class PostProcessUtils(object):
    """후처리 함수"""

    def __init__(self):
        """ 생성자 """
        self.parser = HtmlParser()
        self.job_queue = queue.Queue()

    def insert_job(self, document, post_process_list):
        """스레드 큐에 문서와 할일을 저장한다."""

        if post_process_list is None:
            return

        # 파싱 에러인 경우
        if 'parsing_error' in document and document['parsing_error'] is True:
            return

        # 스래드로 작업 시작
        job = {
            'document': document,
            'post_process_list': post_process_list
        }

        # queue 목록에 작업 저장
        start_thread = False
        if self.job_queue.empty() is True:
            start_thread = True

            log_msg = {
                'level': 'INFO',
                'message': '크롤링 후처리 저장 큐에 저장',
                'queue_size': self.job_queue.qsize(),
            }
            logger.info(msg=LogMsg(log_msg))

            self.job_queue.put(job)
        else:
            self.job_queue.put(job)

        # 스래드 시작
        if start_thread is True:
            thread = threading.Thread(target=self.batch)
            thread.daemon = True
            thread.start()

        return

    def batch(self):
        """후처리 모듈을 실행한다."""

        if self.job_queue.empty() is True:
            return True

        while self.job_queue.empty() is False:
            # 작업 큐에서 작업을 가져온다.
            job = self.job_queue.get()

            document = job['document']
            post_process_list = job['post_process_list']

            for item in post_process_list:
                if item['module'] == 'corpus_process':
                    self.corpus_process(document=document, info=item)
                elif item['module'] == 'save_s3':
                    self.save_s3(document=document, info=item)
                elif item['module'] == 'rabbit_mq':
                    self.rabbit_mq(document=document, info=item)

        return

    @staticmethod
    def rabbit_mq(document, info):
        """ Rabbit MQ로 메세지를 보낸다. """
        import pika

        if document is None:
            return False

        payload = {
            'id': datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f'),
            'document': document
        }
        try:
            if 'payload' in info:
                payload.update(info['payload'])
        except Exception as e:
            log_msg = {
                'level': 'ERROR',
                'message': 'Rabbit MQ payload 파싱 에러',
                'payload': info['payload'],
                'exception': str(e),
            }
            logger.error(msg=LogMsg(log_msg))

            return False

        # 메세지 바디 생성
        try:
            body = bz2.compress(pickle.dumps(payload))
            if 'publish' in info:
                publish_info = info['publish']
                if 'serializer' in publish_info and publish_info['serializer'] == 'json':
                    body = json.dumps(payload, ensure_ascii=False)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'RabbitMQ 메세지 생성 에러',
                'info': info,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

            return False

        doc_url = ''
        if 'url' in document:
            doc_url = document['url']

        # 메세지 전달
        try:
            credentials = pika.PlainCredentials(username=info['host']['user_name'],
                                                password=info['host']['user_password'])

            params = pika.ConnectionParameters(host=info['host']['name'],
                                               port=info['host']['port'],
                                               credentials=credentials)

            with pika.BlockingConnection(params) as connection:
                channel = connection.channel()

                channel.exchange_declare(exchange=info['exchange']['name'],
                                         exchange_type=info['exchange']['type'],
                                         durable=True)

                channel.basic_publish(exchange=info['exchange']['name'],
                                      routing_key='#',
                                      body=body)

                log_msg = {
                    'level': 'MESSAGE',
                    'message': 'RabbitMQ 메세지 전달 성공',
                    'exchange_name': info['exchange']['name'],
                    'doc_url': doc_url,
                }
                logger.log(level=MESSAGE, msg=LogMsg(log_msg))
        except Exception as e:
            log_msg = {
                'level': 'ERROR',
                'message': 'RabbitMQ 전달 에러',
                'doc_url': doc_url,
                'info': info,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(log_msg))

        return True

    @staticmethod
    def convert_datetime(document):
        """ 입력받은 문서에서 데이터 타입이 datetime 를 문자열로 변환한다."""
        for k in document:
            item = document[k]

            if isinstance(item, datetime):
                document[k] = item.strftime('%Y-%m-%dT%H:%M:%S')

        return document

    def corpus_process(self, document, info):
        """ 코퍼스 저처리 분석 데몬에 문서를 전달한다. """
        if document is None:
            return False

        body = {
            'index': info['index'],
            'update': True,
            'doc_type': 'doc',
            'target_url': info['target_url'],
            'document': self.convert_datetime(document)
        }

        headers = {'Content-Type': 'application/json'}
        try:
            url = info['host']
            requests.post(url=url, json=body, headers=headers,
                          allow_redirects=True, timeout=30, verify=False)

            msg = {
                'level': 'MESSAGE',
                'message': '코퍼스 전처리 전달',
                'url': url,
                'id': document['document_id'],
                'title': document['title'],
            }

            logger.log(level=MESSAGE, msg=LogMsg(msg))
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '코퍼스 전처리 에러',
                'id': document['document_id'],
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        return True

    def save_s3(self, document, info):
        """ S3에 기사 이미지를 저장한다."""
        import boto3

        from bs4 import BeautifulSoup
        from botocore.exceptions import ClientError

        # 이미지 목록 추출
        image_list = None
        if 'image_list' in document:
            image_list = document['image_list']
        else:
            if 'html_content' in document:
                soup = BeautifulSoup(document['html_content'], 'lxml')
                image_list = self.parser.extract_image(soup=soup, base_url=document['url'])

        # 추출된 이미지 목록이 없을 경우
        if image_list is None:
            log_msg = {
                'level': 'INFO',
                'message': 'AWS S3 추출된 이미지 없음',
            }
            logger.info(msg=LogMsg(log_msg))
            return

        # api 메뉴얼: http://boto3.readthedocs.io/en/latest/reference/services/s3.html
        bucket_name = info['bucket']
        aws_access_key_id = os.getenv('S3_ACCESS_KEY', 'AKIAI5X5SF6WJK3SFXDA')
        aws_secret_access_key = os.getenv('S3_SECRET_ACCESS_KEY', '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')

        s3 = boto3.resource('s3',
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)

        bucket = s3.Bucket(bucket_name)

        # 이미지 목록
        count = 0
        prefix = document['document_id']
        for image in image_list:
            url = image['image']

            # 이미지 확장자 추출
            suffix = pathlib.Path(url).suffix

            # 1. 이미지 파일 다운로드
            r = requests.get(url)

            upload_file = '{}/{}-{:02d}{}'.format(info['path'], prefix, count, suffix)
            count += 1

            # 파일 확인
            file_exists = False
            try:
                s3.Object(bucket_name, upload_file).get()
                file_exists = True
            except ClientError as e:
                log_msg = {
                    'level': 'INFO',
                    'message': 'AWS S3 파일 확인 에러',
                    'bucket_name': bucket_name,
                    'exception': str(e),
                }
                logger.info(msg=LogMsg(log_msg))

            if file_exists is True:
                # cdn 이미지 주소 추가
                image['cdn_image'] = '{}/{}'.format(info['url_prefix'], upload_file)
                continue

            # 2. s3에 업로드
            try:
                response = bucket.put_object(Key=upload_file, Body=r.content, ACL='public-read',
                                             ContentType=r.headers['content-type'])

                log_msg = {
                    'level': 'INFO',
                    'message': 'AWS S3 이미지 저장 성공',
                    'upload_file': upload_file,
                    'cdn_image': image['cdn_image'],
                    'response': response,
                }
                logger.info(msg=LogMsg(log_msg))

                # cdn 이미지 주소 추가
                image['cdn_image'] = '{}/{}'.format(info['url_prefix'], upload_file)
            except Exception as e:
                log_msg = {
                    'level': 'ERROR',
                    'message': 'AWS S3 이미지 저장 에러',
                    'upload_file': upload_file,
                    'bucket_name': bucket_name,
                    'cdn_image': image['cdn_image'],
                    'exception': str(e),
                }
                logger.error(msg=LogMsg(log_msg))

        # 이미지 목록 업데이트
        document['image_list'] = image_list

        return document
