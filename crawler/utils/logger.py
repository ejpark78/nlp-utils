#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging
import sys
from datetime import datetime

import pytz


class LogMessage(object):
    """구조화된 로깅"""

    def __init__(self, message, **kwargs):
        self.message = message
        self.kwargs = kwargs

        self.timezone = pytz.timezone('Asia/Seoul')

    def __str__(self):
        """문자열로 반환"""
        self.message.update(self.kwargs)

        try:
            if '@timestemp' not in self.message:
                self.message['@timestemp'] = datetime.now(self.timezone).isoformat()

            return json.dumps(self.message, ensure_ascii=False, sort_keys=True)
        except Exception as e:
            return '{0}:{1}'.format(str(self.message), str(e))


class Logger(object):

    def __init__(self):
        super().__init__()

        self.MESSAGE = 25
        self.logger = self.get_logger()

    def get_logger(self):
        """로거를 반환한다."""
        # file_handler = logging.FileHandler(filename='tmp.log')

        logging_opt = {
            'format': '[%(levelname)-s] %(message)s',
            'handlers': [logging.StreamHandler(sys.stderr)],
            'level': self.MESSAGE,
        }

        logging.addLevelName(self.MESSAGE, 'MESSAGE')
        logging.basicConfig(**logging_opt)

        self.logger = logging.getLogger()

        self.logger.setLevel(self.MESSAGE)
        # self.logger.handlers = [logging.StreamHandler(sys.stdout)]

        return self.logger

    def error(self, msg):
        """ 에러 메세지를 출력한다."""
        self.logger.error(msg=LogMessage(msg))
        return

    def info(self, msg):
        """ 메세지를 출력한다."""
        self.logger.info(msg=LogMessage(msg))
        return

    def log(self, msg):
        """ 로그 메세지를 출력한다."""
        self.logger.log(level=self.MESSAGE, msg=LogMessage(msg))
        return

    def debug(self, msg):
        """ 로그 메세지를 출력한다."""
        self.logger.debug(msg=LogMessage(msg))
        return
