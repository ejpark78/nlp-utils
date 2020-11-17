#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
import pickle
import sys
from datetime import datetime
from io import BufferedReader

import urllib3
from dateutil.parser import parse as parse_date
from tqdm import tqdm

from utils.logging_format import LogMessage as LogMsg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)

logger = logging.getLogger()


class CorpusProcessorClient(object):
    """코퍼스 전처리 클라이언트"""

    def __init__(self):
        """생성자"""
        self.connection = {}
        self.channel = {}

    def __exit__(self, exc_type, exc_val, exc_tb):
        """종료시 연결 정보를 정리한다."""
        for host in self.connection:
            try:
                self.channel[host].close()
                del self.channel[host]
            except Exception as e:
                msg = {
                    'level': 'ERROR',
                    'host': host,
                    'exception': str(e),
                }
                logger.error(msg=LogMsg(msg))

            try:
                self.connection[host].close()
                del self.connection[host]
            except Exception as e:
                msg = {
                    'level': 'ERROR',
                    'host': host,
                    'exception': str(e),
                }
                logger.error(msg=LogMsg(msg))

        return

    def rabbit_mq(self, document, info):
        """ RabbitMQ로 메세지를 보낸다. """
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
            msg = {
                'level': 'ERROR',
                'message': 'RabbitMQ payload 파싱 에러',
                'payload': info['payload'],
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        doc_url = ''
        if 'url' in document:
            doc_url = document['url']

        host = info['host']['name']

        # connection, channel 생성
        if host not in self.connection:
            try:
                credentials = pika.PlainCredentials(username=info['host']['user_name'],
                                                    password=info['host']['user_password'])

                params = pika.ConnectionParameters(host=info['host']['name'],
                                                   port=info['host']['port'],
                                                   credentials=credentials)

                self.connection[host] = pika.BlockingConnection(params)
                self.channel[host] = self.connection[host].channel()
            except Exception as e:
                msg = {
                    'level': 'ERROR',
                    'message': 'RabbitMQ 연결 에러',
                    'exception': str(e),
                }
                logger.error(msg=LogMsg(msg))

        # 메세지 전달
        try:
            properties = None
            if 'reply' in info['exchange'] and info['exchange']['reply'] != '':
                properties = pika.BasicProperties(
                    reply_to=info['exchange']['reply'],
                )

            body = bz2.compress(pickle.dumps(payload))
            self.channel[host].exchange_declare(
                exchange=info['exchange']['name'],
                exchange_type=info['exchange']['type'],
                durable=True,
            )

            self.channel[host].basic_publish(
                exchange=info['exchange']['name'],
                routing_key='#',
                body=body,
                properties=properties,
            )

            msg = {
                'level': 'INFO',
                'message': 'RabbitMQ 전달 성공',
                'exchange_name': info['exchange']['name'],
                'doc_url': doc_url,
            }
            logger.info(msg=LogMsg(msg))
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'RabbitMQ 전달 에러',
                'doc_url': doc_url,
                'info': info,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))

        return True

    def web_news(self, doc, host, mq_host, index):
        """웹 뉴스를 분석한다."""
        if 'meta' in doc:
            del doc['meta']

        for k in ['date', 'insert_date', 'curl_date']:
            if k in doc and '$date' in doc[k]:
                doc[k] = parse_date(doc[k]['$date'])

        if 'url' in doc and 'full' in doc['url']:
            max_try = 10
            while 'full' in doc['url']:
                doc['url'] = doc['url']['full']

                max_try -= 1
                if max_try < 0:
                    break

        mq_config = {
            'exchange': {
                'type': 'topic',
                'name': 'crawler.batch',
            },
            'host': {
                'name': mq_host,
                'port': 5672,
                'user_name': 'user',
                'user_password': 'nlplab!',
            },
            'payload': {
                'elastic': {
                    'host': 'http://{}:9200'.format(host),
                    'index': index,
                },
            },
        }

        self.rabbit_mq(doc, info=mq_config)

        return

    def one_text(self, doc, mq_host, index):
        """문장/문서를 분석한다."""
        tbl = index.replace('-', '_')
        filename = 'data/{hostname}/' + index + '.{date}.db'

        mq_config = {
            'exchange': {
                'type': 'topic',
                'name': 'text.game',
                'reply': 'corpus_processor.reply',
            },
            'host': {
                'name': mq_host,
                'port': 5672,
                'user_name': 'user',
                'user_password': 'nlplab!'
            },
            'payload': {
                'sqlite': {
                    'table': tbl,
                    'filename': filename,
                    'date_format': '%Y-%m-%d_%H',
                },
                'doc_type': 'text',
                'module': [
                    {
                        'name': 'sp/pos_tagger',
                        'domain': 'game',
                        'column': 'text',
                        'result': 'pos_tagged',
                    },
                    {
                        'name': 'nc/ne_tagger_v2',
                        'domain': 'game',
                        'column': 'text',
                        'result': 'named_entity_v2',
                    }
                ]
            },
        }

        if len(doc) == 1:
            self.rabbit_mq(doc[0], info=mq_config)
        else:
            self.rabbit_mq(doc, info=mq_config)

        return

    def text(self, filename, tag, host_list):
        """텍스트를 분석한다."""
        with open(host_list, 'r') as fp:
            mq_list = [h.strip() for h in fp.readlines()]

        i = 0
        msg = {
            'level': 'MESSAGE',
            'message': '텍스트 분석 시작',
            'filename': filename,
            'tag': tag,
            'host_list': host_list,
            'mq_list': mq_list,
        }
        logger.log(level=MESSAGE, msg=msg)

        bulk_size = 0
        bulk_data = list()

        with bz2.open(filename, 'rb') as fp:
            bfp = BufferedReader(fp)

            for line in tqdm(bfp.readlines()):
                line = str(line, 'utf-8')

                doc = json.loads(line)

                bulk_data.append(doc)
                if bulk_size > len(bulk_data):
                    continue

                i += 1
                if i >= len(mq_list):
                    i = 0

                self.one_text(bulk_data, mq_list[i], tag)
                bulk_data = list()

            if len(bulk_data) > 0:
                self.one_text(bulk_data, mq_list[i], tag)

        return

    def one_bbs(self, doc, mq_host, index):
        """문장/문서를 분석한다."""
        tbl = index.replace('-', '_')
        filename = 'data/{hostname}/' + index + '.{date}.db'

        mq_config = {
            'exchange': {
                'type': 'topic',
                'name': 'text.game',
                'reply': 'corpus_processor.reply',
            },
            'host': {
                'name': mq_host,
                'port': 5672,
                'user_name': 'user',
                'user_password': 'nlplab!',
            },
            'payload': {
                'reply': {
                    'index': index,
                },
                # 'sqlite': {
                #     'table': tbl,
                #     'filename': filename,
                #     'date_format': '%Y-%m-%d_%H',
                # },
                'doc_type': 'bbs',
                'module': [
                    {
                        'name': 'sp/pos_tagger',
                        'domain': 'game',
                        'column': 'title',
                        'result': 'title_pos_tagged',
                    },
                    {
                        'name': 'sp/pos_tagger',
                        'domain': 'game',
                        'column': 'contents',
                        'result': 'contents_pos_tagged',
                    },
                    {
                        'name': 'sp/pos_tagger',
                        'domain': 'game',
                        'column': 'comment_list',
                        'result': 'contents_pos_tagged',
                    },
                    {
                        'name': 'nc/ne_tagger_v2',
                        'domain': 'game',
                        'column': 'title',
                        'result': 'title_named_entity_v2',
                    },
                    {
                        'name': 'nc/ne_tagger_v2',
                        'domain': 'game',
                        'column': 'contents',
                        'result': 'contents_named_entity_v2',
                    },
                    {
                        'name': 'nc/ne_tagger_v2',
                        'domain': 'game',
                        'column': 'comment_list',
                        'result': 'contents_named_entity_v2',
                    },
                ],
            },
        }

        if len(doc) == 1:
            self.rabbit_mq(doc[0], info=mq_config)
        else:
            self.rabbit_mq(doc, info=mq_config)

        return

    def bbs(self, filename, tag, host_list):
        """게시판을 분석한다."""
        from utils.lineagem import LineageMBbsUtils

        utils = LineageMBbsUtils()

        with open(host_list, 'r') as fp:
            mq_list = [h.strip() for h in fp.readlines()]

        i = 0
        msg = {
            'level': 'MESSAGE',
            'message': '게시판 분석 시작',
            'filename': filename,
            'tag': tag,
            'host_list': host_list,
            'mq_list': mq_list,
        }
        logger.log(level=MESSAGE, msg=msg)

        bulk_size = 0
        bulk_data = list()

        with bz2.open(filename, 'rb') as fp:
            bfp = BufferedReader(fp)

            for line in tqdm(bfp.readlines()):
                line = str(line, 'utf-8')

                doc = json.loads(line)

                if 'contents' in doc:
                    doc['contents'] = utils.get_clean_text(doc['contents'])

                bulk_data.append(doc)
                if bulk_size > len(bulk_data):
                    continue

                i += 1
                if i >= len(mq_list):
                    i = 0

                self.one_bbs(bulk_data, mq_host=mq_list[i], index=tag)
                bulk_data = list()

            if len(bulk_data) > 0:
                self.one_bbs(bulk_data, mq_host=mq_list[i], index=tag)

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('-bbs', action='store_true', default=False, help='')
        parser.add_argument('-text', action='store_true', default=False, help='')

        parser.add_argument('-filename', default='', help='')
        parser.add_argument('-tag', default='', help='')
        parser.add_argument('-host_list', default='', help='')

        return parser.parse_args()


def main():
    """ """
    utils = CorpusProcessorClient()
    args = utils.init_arguments()

    if args.text:
        utils.text(filename=args.filename, tag=args.tag, host_list=args.host_list)

    if args.bbs:
        utils.bbs(filename=args.filename, tag=args.tag, host_list=args.host_list)

    return


if __name__ == '__main__':
    main()
