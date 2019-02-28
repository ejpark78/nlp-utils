#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
from datetime import datetime


class LogMessage(object):
    """"""

    def __init__(self, message, **kwargs):
        """"""
        self.message = message
        self.kwargs = kwargs

    def __str__(self):
        """"""
        self.message.update(self.kwargs)
        self.message['log_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return json.dumps(self.message, ensure_ascii=False, sort_keys=True)
