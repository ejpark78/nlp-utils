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

    @staticmethod
    def save_excel(filename, data, columns):
        """ 크롤링 결과를 엑셀로 저장한다. """
        from openpyxl import Workbook

        status = []
        wb = Workbook()

        for path in data:
            count = '{:,}'.format(len(data[path]))
            status.append([path, count])

            ws = wb.create_sheet(path.replace('/', '-'))

            if len(columns) == 0:
                columns = list(data[path][0].keys())

            ws.append(columns)
            for doc in data[path]:
                lines = []
                for c in columns:
                    v = ''
                    if c in doc:
                        v = doc[c]

                    if v is None:
                        v = ''

                    lines.append('{}'.format(v))

                ws.append(lines)

        # 통계 정보 저장
        ws = wb['Sheet']
        for row in status:
            ws.append(row)

        ws.title = 'status'

        # 파일 저장
        wb.save(filename)

        return
