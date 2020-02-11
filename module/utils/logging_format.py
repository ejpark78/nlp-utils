#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
from datetime import datetime

import pytz


class LogMessage(object):
    """구조화된 로깅"""

    def __init__(self, message, **kwargs):
        """생성자"""
        self.message = message
        self.kwargs = kwargs

        self.timezone = pytz.timezone('Asia/Seoul')

    def __str__(self):
        """문자열로 반환"""
        self.message.update(self.kwargs)

        try:
            if 'logging_date' not in self.message:
                self.message['logging_date'] = datetime.now(self.timezone).isoformat()

            return json.dumps(self.message, ensure_ascii=False, sort_keys=True)
        except Exception as e:
            return str(self.message)
