#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging

from kombu import Connection, Exchange, Consumer, Queue, eventloop

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


def pretty(obj):
    return json.dumps(obj, indent=4, ensure_ascii=False)


def handle_message(body, message):
    print('Received message:')
    print('  properties:\n{0}'.format(pretty(message.properties)))
    print('  delivery_info:\n{0}'.format(pretty(message.delivery_info)))
    print('  body:\n{0}'.format(pretty(body)))
    message.ack()


if __name__ == '__main__':

    info = {
        "exchange": {
            "type": "topic",
            "name": "crawler/naver_terms_detail"
        },
        "host": "amqp://user:nlplab!@koala.korea.ncsoft.corp:5672//"
    }

    connection = Connection(hostname=info['host'])
    exchange = Exchange(name=info['exchange']['name'],
                        type=info['exchange']['type'])

    queue = Queue(name=info['exchange']['name'],
                  exchange=exchange)

    with Consumer(connection,
                  queues=queue,
                  callbacks=[handle_message],
                  accept=['pickle']) as consumer:
        for _ in eventloop(connection):
            pass
