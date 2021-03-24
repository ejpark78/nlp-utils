#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
import pickle
import socket
from time import sleep

import pika

from config import config
from logging_format import LogMessage as LogMsg
from utils.corpus_pipeline_utils import CorpusPipelineUtils

MESSAGE = 25
logger = logging.getLogger('mq')

is_reachable = False
corpus_processor_utils = CorpusPipelineUtils()


def callback(ch, method, properties, body):
    """코퍼스 전처리"""
    global corpus_processor_utils

    payload = pickle.loads(bz2.decompress(body))

    doc_info = {}

    try:
        for k in ['document_id', 'title', 'url']:
            if k in payload['document']:
                doc_info[k] = payload['document'][k]
    except Exception as e:
        msg = {
            'level': 'ERROR',
            'message': '필수 컬럼 추출 오류',
            'exception': str(e),
        }
        msg.update(doc_info)

        logger.error(msg=LogMsg(msg))

    # 문서 분석 시작
    document = None

    is_error = False
    try:
        document = corpus_processor_utils.batch(payload=payload)
    except Exception as e:
        msg = {
            'level': 'ERROR',
            'message': '코퍼스 전처리 에러 (batch)',
            'exception': str(e),
        }
        msg.update(doc_info)

        logger.error(msg=LogMsg(msg))
        is_error = True

    if is_error is False:
        msg = {
            'level': 'MESSAGE',
            'message': '코퍼스 전처리 성공',
        }
        msg.update(doc_info)
        logger.log(level=MESSAGE, msg=LogMsg(msg))

    # reply_to 가 있는 경우
    try:
        if properties.reply_to is None:
            msg = {
                'level': 'INFO',
                'message': 'reply_to 가 None 임',
                'properties': properties,
            }
            logger.info(msg=LogMsg(msg))
            return

        if 'reply' not in payload:
            msg = {
                'level': 'ERROR',
                'message': 'reply 가 payload 에 없음',
                'payload': payload,
            }
            logger.error(msg=LogMsg(msg))
            return

        ch.exchange_declare(
            exchange=properties.reply_to,
            exchange_type='topic',
            durable=True,
        )

        document['index'] = payload['reply']['index']

        ch.basic_publish(
            exchange=properties.reply_to,
            routing_key='#',
            body=json.dumps(document),
        )
    except Exception as e:
        msg = {
            'level': 'ERROR',
            'message': 'reply 에러',
            'exception': str(e),
            'properties': properties,
        }
        logger.error(msg=LogMsg(msg))

    return


def wait_mq_init(host, port):
    """mq가 초기화될 때까지 기다린다."""
    global is_reachable

    if is_reachable is True:
        return

    ping_counter = 0
    while is_reachable is False and ping_counter < 5:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((host, port))

                is_reachable = True
            except socket.error as e:
                msg = {
                    'level': 'INFO',
                    'message': 'RabbitMQ 접속 대기 {}'.format(ping_counter),
                    'exception': str(e),
                }
                logger.info(msg=LogMsg(msg))

                sleep(2)

                ping_counter += 1

    return


def consumer():
    """Rabbit MQ consumer"""
    global corpus_processor_utils

    host_info = config['consumer']['host']

    # 접속 대기
    wait_mq_init(
        host=host_info['name'],
        port=host_info['port'],
    )

    credentials = pika.PlainCredentials(
        username=host_info['user_name'],
        password=host_info['user_password'],
    )

    params = pika.ConnectionParameters(
        host=host_info['name'],
        port=host_info['port'],
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)

    channel = connection.channel()

    exchange_info = config['consumer']['exchange']
    channel.exchange_declare(
        exchange=exchange_info['name'],
        exchange_type=exchange_info['type'],
        durable=True,
    )

    result = channel.queue_declare(
        queue=exchange_info['name'],
        durable=True,
    )

    queue_name = result.method.queue
    channel.queue_bind(
        exchange=exchange_info['name'],
        queue=queue_name,
        routing_key='#',
    )

    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        auto_ack=True,
    )

    msg = {
        'level': 'MESSAGE',
        'message': '데몬 시작',
        'queue_name': queue_name,
        'host_info': host_info,
        'exchange_info': exchange_info,
    }
    logger.log(level=MESSAGE, msg=LogMsg(msg))

    try:
        channel.start_consuming()
    except e:
        pass

    return
