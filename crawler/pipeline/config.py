#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging.basicConfig(
    format="[%(levelname)-s] %(message)s",
    handlers=[logging.StreamHandler()],
    level=MESSAGE,
)

plugins = {
    'list': [],
    'debug_info': {},
}

config = {
    'port': int(os.getenv('PORT', 80)),
    'debug': int(os.getenv('DEBUG', 0)),
    'hostname': os.getenv('HOSTNAME', 'cp'),
    'nlu_wrapper': os.getenv('NLU_WRAPPER_URL', 'http://172.20.78.250:30000'),
    'consumer': {
        'enable': int(os.getenv('USE_CONSUMER', 1)),
        'host': {
            'name': os.getenv('CONSUMER_HOST', 'g7'),
            'port': int(os.getenv('CONSUMER_PORT', 5672)),
            'user_name': os.getenv('CONSUMER_USER_NAME', 'user'),
            'user_password': os.getenv('CONSUMER_USER_PASSWD', 'nlplab!'),
        },
        'exchange': {
            'type': os.getenv('CONSUMER_EXCHANGE_TYPE', 'topic'),
            'name': os.getenv('CONSUMER_EXCHANGE_NAME', 'corpus-pipeline'),
        },
        'publish': {
            'serializer': os.getenv('CONSUMER_SERIALIZER', 'bzip2'),
        }
    }
}
