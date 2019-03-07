#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json


class LogMessage(object):
    """구조화된 로깅"""

    def __init__(self, message, **kwargs):
        """생성자"""
        self.message = message
        self.kwargs = kwargs

    def __str__(self):
        """문자열로 반환"""
        self.message.update(self.kwargs)

        try:
            return json.dumps(self.message, ensure_ascii=False, sort_keys=True)
        except Exception as e:
            return str(self.message)
