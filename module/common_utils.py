#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')


class CommonUtils(object):
    """"""

    def __init__(self):
        """ 생성자 """

    @staticmethod
    def print_message(msg):
        """화면에 메세지를 출력한다."""
        try:
            str_msg = json.dumps(msg, ensure_ascii=False, sort_keys=True)
            logging.log(level=MESSAGE, msg=str_msg)
        except Exception as e:
            logging.info(msg='{}'.format(e))

        return
