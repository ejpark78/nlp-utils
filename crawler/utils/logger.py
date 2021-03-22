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

    def __init__(self, message: dict, show_date: bool = True, **kwargs):
        self.message = message
        self.show_logging_date = show_date

        self.kwargs = kwargs

        self.timezone = pytz.timezone('Asia/Seoul')

    def __str__(self):
        self.message.update(self.kwargs)

        try:
            if self.show_logging_date is True and 'logging_date' not in self.message:
                self.message['logging_date'] = datetime.now(self.timezone).isoformat()

            return json.dumps(self.message, ensure_ascii=False, sort_keys=True, default=self.convert_date)
        except Exception as e:
            return '{0}:{1}'.format(str(self.message), str(e))

    @staticmethod
    def convert_date(obj: any) -> str:
        if isinstance(obj, datetime):
            return obj.isoformat()

        raise TypeError(f'[ERROR] JSON serializable: {obj}')


class Logger(object):

    def __init__(self):
        super().__init__()

        self.MESSAGE = 25
        self.logger = self.get_logger()

    def get_logger(self):
        logging_opt = {
            'format': '%(message)s',
            'handlers': [logging.StreamHandler(sys.stderr)],
            'level': self.MESSAGE,
        }

        logging.addLevelName(self.MESSAGE, 'MESSAGE')
        logging.basicConfig(**logging_opt)

        self.logger = logging.getLogger()

        self.logger.setLevel(self.MESSAGE)
        # self.logger.handlers = [logging.StreamHandler(sys.stderr)]

        return self.logger

    def error(self, msg: dict, show_date: bool = True) -> None:
        self.logger.error(msg=LogMessage(msg, show_date=show_date))
        return

    def info(self, msg: dict, show_date: bool = True) -> None:
        self.logger.info(msg=LogMessage(msg, show_date=show_date))
        return

    def log(self, msg: dict, show_date: bool = True) -> None:
        self.logger.log(level=self.MESSAGE, msg=LogMessage(msg, show_date=show_date))
        return

    def warning(self, msg: dict, show_date: bool = True) -> None:
        self.logger.warning(msg=LogMessage(msg, show_date=show_date))
        return

    def debug(self, msg: dict, show_date: bool = True) -> None:
        self.logger.debug(msg=LogMessage(msg, show_date=show_date))
        return
