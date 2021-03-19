#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import smtplib
from datetime import datetime

import pytz
import urllib3
from email.message import EmailMessage
from os.path import isfile

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class SmtpRely(object):

    def __init__(self):
        super().__init__()

        self.today = datetime.now(tz=pytz.timezone('Asia/Seoul'))

    def batch(self) -> None:
        params = self.init_arguments()

        today = self.today.strftime('%Y-%m-%d')

        message = EmailMessage()

        with open('reports.html', 'r') as fp:
            message.add_alternative(''.join(fp.readlines()), subtype='html')

        if isfile(params['attach']):
            with open(params['attach'], 'rb') as fp:
                data = fp.read()
                message.add_attachment(
                    data,
                    maintype='application',
                    subtype='pdf',
                    filename=params['attach'].split('/')[-1]
                )

        message['From'] = params['from']
        message['To'] = params['to'].split(',')
        message['Subject'] = f'[Crawler Daily Reports] {today}'

        # Send the mail
        with smtplib.SMTP(params['server']) as server:
            server.send_message(message)

        return

    @staticmethod
    def init_arguments() -> dict:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--server', default='172.20.0.116', type=str, help='SMTP Rely Server')

        parser.add_argument('--from', default='ejpark@ncsoft.com', type=str, help='보내이')
        parser.add_argument('--to', default='ejpark@ncsoft.com', type=str, help='받는이')

        parser.add_argument('--contents', default='./reports.html', type=str, help='메일 본문')
        parser.add_argument('--attach', default=None, type=str, help='첨부파일')

        return vars(parser.parse_args())


if __name__ == '__main__':
    SmtpRely().batch()
