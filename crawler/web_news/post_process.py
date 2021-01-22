#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import pickle
import queue
import socket
import threading
from datetime import datetime
from time import sleep

import pytz
import requests

from crawler.utils.html_parser import HtmlParser
from crawler.utils.logger import Logger


class PostProcessUtils(object):
    """후처리 함수"""

    def __init__(self):
        self.logger = Logger()

        self.parser = HtmlParser()
        self.job_queue = queue.Queue()

        self.is_reachable = False

        self.timezone = pytz.timezone('Asia/Seoul')

    def insert_job(self, document: dict, post_process_list: list, job: dict) -> None:
        """스레드 큐에 문서와 할일을 저장한다."""

        if document is None:
            return

        if post_process_list is None:
            return

        # 파싱 에러인 경우
        if 'parsing_error' in document and document['parsing_error'] is True:
            return

        # 스래드로 작업 시작
        thread_job = {
            'job': job,
            'document': document,
            'post_process_list': post_process_list
        }

        # queue 목록에 작업 저장
        start_thread = False
        if self.job_queue.empty() is True:
            start_thread = True

            self.logger.info(msg={
                'level': 'INFO',
                'message': '크롤링 후처리 저장 큐에 저장',
                'queue_size': self.job_queue.qsize(),
            })

            self.job_queue.put(thread_job)
        else:
            self.job_queue.put(thread_job)

        # 스래드 시작
        if start_thread is True:
            thread = threading.Thread(target=self.batch)
            thread.daemon = True
            thread.start()

        return

    def batch(self) -> bool:
        """후처리 모듈을 실행한다."""

        if self.job_queue.empty() is True:
            return True

        while self.job_queue.empty() is False:
            # 작업 큐에서 작업을 가져온다.
            job = self.job_queue.get()

            document = job['document']
            post_process_list = job['post_process_list']

            for item in post_process_list:
                # elasticsearch 의 이름을 실제 아이피값으로 변환한다.
                # self.update_hostname2ip(item)

                if item['module'] == 'corpus_process':
                    self.corpus_process(document=document, info=item)
                elif item['module'] == 'rabbit_mq':
                    self.rabbit_mq(document=document, info=item)

        return True

    def wait_mq_init(self, host: str, port: str) -> None:
        """mq가 초기화될 때까지 기다린다."""
        if self.is_reachable is True:
            return

        ping_counter = 0
        while self.is_reachable is False and ping_counter < 5:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((host, port))

                    self.is_reachable = True
                except socket.error as e:
                    self.logger.info(msg={
                        'level': 'INFO',
                        'message': 'RabbitMQ 접속 대기 {}'.format(ping_counter),
                        'exception': str(e),
                    })

                    sleep(2)

                    ping_counter += 1

        return

    def rabbit_mq(self, document: dict, info: dict) -> bool:
        """ Rabbit MQ로 메세지를 보낸다. """
        import pika

        if document is None:
            return False

        # rabbit mq 접속 대기
        self.wait_mq_init(
            host=info['host']['name'],
            port=info['host']['port'],
        )

        payload = {
            'id': datetime.now(self.timezone).isoformat(),
            'document': document
        }
        try:
            if 'payload' in info:
                payload.update(info['payload'])
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'Rabbit MQ payload 파싱 에러',
                'payload': info['payload'],
                'exception': str(e),
            })

            return False

        # 메세지 바디 생성
        try:
            body = bz2.compress(pickle.dumps(payload))
            if 'publish' in info:
                publish_info = info['publish']
                if 'serializer' in publish_info and publish_info['serializer'] == 'json':
                    body = json.dumps(payload, ensure_ascii=False)
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'RabbitMQ 메세지 생성 에러',
                'info': info,
                'exception': str(e),
            })

            return False

        doc_url = ''
        if 'url' in document:
            doc_url = document['url']

        # 메세지 전달
        try:
            credentials = pika.PlainCredentials(
                username=info['host']['user_name'],
                password=info['host']['user_password'],
            )

            params = pika.ConnectionParameters(
                host=info['host']['name'],
                port=info['host']['port'],
                credentials=credentials,
            )

            with pika.BlockingConnection(params) as connection:
                channel = connection.channel()

                channel.exchange_declare(
                    exchange=info['exchange']['name'],
                    exchange_type=info['exchange']['type'],
                    durable=True,
                )

                channel.basic_publish(
                    exchange=info['exchange']['name'],
                    routing_key='#',
                    body=body,
                )

                self.logger.log(msg={
                    'level': 'MESSAGE',
                    'message': 'RabbitMQ 메세지 전달 성공',
                    'exchange_name': info['exchange']['name'],
                    'doc_url': doc_url,
                })
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': 'RabbitMQ 전달 에러',
                'doc_url': doc_url,
                'info': info,
                'exception': str(e),
            })

        return True

    @staticmethod
    def convert_datetime(document: dict) -> dict:
        """ 입력받은 문서에서 데이터 타입이 datetime 를 문자열로 변환한다."""
        for k in document:
            item = document[k]

            if isinstance(item, datetime):
                document[k] = item.isoformat()

        return document

    def corpus_process(self, document: dict, info: dict) -> bool:
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
            requests.post(
                url=url,
                json=body,
                headers=headers,
                allow_redirects=True,
                timeout=30,
                verify=False,
            )

            self.logger.log(msg={
                'level': 'MESSAGE',
                'message': '코퍼스 전처리 전달',
                'url': url,
                'id': document['document_id'],
                'title': document['title'],
            })
        except Exception as e:
            self.logger.error(msg={
                'level': 'ERROR',
                'message': '코퍼스 전처리 에러 (api)',
                'id': document['document_id'],
                'exception': str(e),
            })

        return True
