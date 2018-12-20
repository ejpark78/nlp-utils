#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
from datetime import datetime

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class MqProducerUtils(object):
    """"""

    @staticmethod
    def rabbit_mq(document, info):
        """ Rabbit MQ로 메세지를 보낸다. """
        if document is None:
            return False

        from kombu import Connection, Exchange
        from kombu.pools import producers

        payload = {}
        try:
            if 'payload' in info:
                payload = json.loads(info['payload'])
        except Exception as e:
            logging.error('{}'.format(e))

        payload['id'] = datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')
        payload['document'] = document

        retry_policy = {
            'interval_start': 1,
            'interval_step': 2,
            'interval_max': 30,
            'max_retries': 10
        }

        try:
            connection = Connection(hostname=info['host'])
            exchange = Exchange(name=info['exchange']['name'], type=info['exchange']['type'])

            with producers[connection].acquire(block=True) as producer:
                producer.publish(payload,
                                 serializer='pickle',
                                 compression='bzip2',
                                 exchange=exchange,
                                 declare=[exchange],
                                 expiration=21600,
                                 retry=True,
                                 retry_policy=retry_policy)

                msg = 'Rabbit MQ 전달: {}'.format(info['exchange']['name'])
                logging.log(level=MESSAGE, msg=msg)
        except Exception as e:
            msg = 'Rabbit MQ 전달 에러: {}'.format(info['exchange']['name'], e)
            logging.error(msg=msg)

        return True

    def batch(self):
        """"""
        from module.elasticsearch_utils import ElasticSearchUtils

        info = {
            "exchange": {
                "type": "topic",
                "name": "crawler"
            },
            "host": "amqp://user:nlplab!@koala.korea.ncsoft.corp:5672//",
            "payload": "{"
                       "    \"elastic\": {"
                       "       \"host\": \"http://b1:9200\", "
                       "       \"index\": \"corpus_process-major_press-spotvnews\""
                       "    }"
                       "}"
        }

        host = 'http://b1:9200'
        index = 'crawler-major_press-spotvnews'

        elastic_utils = ElasticSearchUtils(host=host, index=index, bulk_size=100)

        # 질문 목록 조회
        doc_list = elastic_utils.dump(index=index, query={}, only_source=True, limit=100)

        count = 0
        for item in doc_list:
            self.rabbit_mq(document=item, info=info)
            print(count)
            count += 1

        return
