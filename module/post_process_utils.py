#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import queue
import threading
from datetime import datetime

import requests

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class PostProcessUtils(object):
    """후처리 함수"""

    def __init__(self):
        """ 생성자 """
        self.job_queue = queue.Queue()

    def insert_job(self, document, post_process_list):
        """스레드 큐에 문서와 할일을 저장한다."""
        # 스래드로 작업 시작
        job = {
            'document': document,
            'post_process_list': post_process_list
        }

        # queue 목록에 작업 저장
        start_thread = False
        if self.job_queue.empty() is True:
            start_thread = True

            logging.info(msg='저장 큐에 저장: {:,}'.format(self.job_queue.qsize()))
            self.job_queue.put(job)
        else:
            self.job_queue.put(job)

        if start_thread is True:
            # 스래드 시작
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
                if item['module'] == 'send_corpus_process':
                    self.send_corpus_process(document=document, info=item)

        return

    @staticmethod
    def convert_datetime(document):
        """ 입력받은 문서에서 데이터 타입이 datetime 를 문자열로 변환한다."""
        for k in document:
            item = document[k]

            if isinstance(item, datetime):
                document[k] = item.strftime('%Y-%m-%dT%H:%M:%S')

        return document

    def send_corpus_process(self, document, info):
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

            msg = '코퍼스 전처리: {} {} {}'.format(url, document['document_id'], document['title'])
            logging.log(level=MESSAGE, msg=msg)
        except Exception as e:
            msg = '코퍼스 전처리 에러: {} {}'.format(document['_id'], e)
            logging.error(msg=msg)

        return True
