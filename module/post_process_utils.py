#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import pathlib
import queue
import threading
from datetime import datetime

import requests

from module.html_parser import HtmlParser

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class PostProcessUtils(object):
    """후처리 함수"""

    def __init__(self):
        """ 생성자 """
        self.parser = HtmlParser()
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
                elif item['module'] == 'save_s3':
                    self.save_s3(document=document, info=item)

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
            msg = '코퍼스 전처리 에러: {} {}'.format(document['document_id'], e)
            logging.error(msg=msg)

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
                logging.info('{}'.format(e))

            if file_exists is True:
                # cdn 이미지 주소 추가
                image['cdn_image'] = '{}/{}'.format(info['url_prefix'], upload_file)
                continue

            # 2. s3에 업로드
            try:
                response = bucket.put_object(Key=upload_file, Body=r.content, ACL='public-read',
                                             ContentType=r.headers['content-type'])
                logging.info(msg='save S3: {}'.format(response))

                # cdn 이미지 주소 추가
                image['cdn_image'] = '{}/{}'.format(info['url_prefix'], upload_file)
            except Exception as e:
                logging.error(msg='s3 저장 오류: {}'.format(e))

        # 이미지 목록 업데이트
        document['image_list'] = image_list

        return document
