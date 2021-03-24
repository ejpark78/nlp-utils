#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys

from config import config
from consumer import consumer
from rest_api import rest_api

MESSAGE = 25

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(format='%(message)s')

root_logger = logging.getLogger()

root_logger.setLevel(MESSAGE)
root_logger.handlers = [logging.StreamHandler(sys.stderr)]

rest_api_logger = logging.getLogger('rest_api')

rest_api_logger.setLevel(MESSAGE)
rest_api_logger.handlers = [logging.StreamHandler(sys.stderr)]

mq_logger = logging.getLogger('mq')

mq_logger.setLevel(MESSAGE)
mq_logger.handlers = [logging.StreamHandler(sys.stderr)]


if __name__ == "__main__":
    """Flask 실행"""
    if config['consumer']['enable'] == 1:
        consumer()
    else:
        rest_api()
