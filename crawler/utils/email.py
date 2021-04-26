#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import isfile

import urllib3
from exchangelib import FileAttachment, Message, Mailbox, HTMLBody, ServiceAccount, Configuration, Account, DELEGATE
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)


class EmailUtils(object):
    """이메일 유틸"""

    def __init__(self):
        pass

    @staticmethod
    def open(user_id, user_password):
        """메일에 연결한다.
        * 참고자료
        - https://stackoverflow.com/questions/43491673
            /read-emails-and-download-attachment-from-microsoft-exchange-server/45438174#45438174
        - https://pypi.org/project/exchangelib/
        """
        BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter

        cfg = {
            'smtp_address': user_id,
            'imap_user': user_id,
            'imap_password': user_password,
            # 'imap_server': 'outlook.office365.com',
            'imap_server': '40.100.2.98',
        }

        credentials = ServiceAccount(
            username=cfg['imap_user'],
            password=cfg['imap_password'],
        )

        config = Configuration(server=cfg['imap_server'], credentials=credentials)
        account = Account(
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
            credentials=credentials,
            primary_smtp_address=cfg['smtp_address'],
        )

        return account

    def send_mail(self, subject, body, email_list, user_id, user_password):
        """메일을 보낸다."""
        # 메일 연결
        account = self.open(user_id, user_password)

        # 메일 받는 사람 생성
        to_recipients = []
        for email in email_list:
            to_recipients.append(Mailbox(email_address=email))

        # 메일 본문 작성
        m = Message(
            account=account,
            subject=subject,
            body=HTMLBody(body),
            to_recipients=to_recipients,
        )

        # 메일 보내기
        m.send()

        return

    @staticmethod
    def attach_file(message, filename):
        """파일을 첨부한다."""
        if isfile(filename) is False:
            return message

        with open(filename, 'rb') as fp:
            f_attach = FileAttachment(name=filename, content=fp.read())
            message.attach(f_attach)

        return message

# if __name__ == '__main__':
#     mail = EmailUtils()
#
#     account = mail.open('ejpark@ncsoft.com', '***')
#
#     print(account.root)
#
#     for item in account.inbox.all().order_by('-datetime_received')[:100]:
#         print(item.subject, item.sender, item.datetime_received)
