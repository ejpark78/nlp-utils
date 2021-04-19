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

        if params['to'] is None:
            return

        # make mail body
        message = EmailMessage()

        with open(params['contents'], 'r') as fp:
            message.add_alternative(''.join(fp.readlines()), subtype='html')

        if params['attach']:
            for filename in params['attach'].split(','):
                if isfile(filename) is False:
                    continue

                with open(filename, 'rb') as fp:
                    subtype = 'pdf'
                    if '.ipynb' in filename:
                        subtype = 'ipynb'

                    message.add_attachment(
                        fp.read(),
                        maintype='application',
                        subtype=subtype,
                        filename=filename.split('/')[-1]
                    )

        message['From'] = params['from']
        message['To'] = params['to'].split(',')
        message['Subject'] = f'{params["subject"]}'

        # Send the mail
        with smtplib.SMTP(params['server']) as server:
            server.send_message(message)

        return

    @staticmethod
    def init_arguments() -> dict:
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--server', default='172.20.0.116', type=str, help='SMTP Rely Server')

        parser.add_argument('--from', default=None, type=str, help='보내이')
        parser.add_argument('--to', default=None, type=str, help='받는이')

        parser.add_argument('--subject', default='[Crawler Daily Reports]', type=str, help='메일 본문')

        parser.add_argument('--contents', default=None, type=str, help='메일 본문')
        parser.add_argument('--attach', default=None, type=str, help='첨부파일')

        return vars(parser.parse_args())


if __name__ == '__main__':
    SmtpRely().batch()
