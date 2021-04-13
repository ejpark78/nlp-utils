#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import sys
from os import makedirs

import pytz
import urllib3
from webdav3.client import Client

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings(UserWarning)

MESSAGE = 25
logging.addLevelName(MESSAGE, 'MESSAGE')

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.basicConfig(**logging_opt)

logger = logging.getLogger()


class NextcloudUtils(object):
    """클라우드 유틸"""

    def __init__(self):
        """ 생성자 """
        self.timezone = pytz.timezone('Asia/Seoul')

        self.webdav_options = {
            'webdav_hostname': 'https://corpus.ncsoft.com:8080/remote.php/dav/files/',
            'webdav_login': 'corpus_center',
            'webdav_password': 'nlplab2019!'
        }

        self.client = None

    def open(self, options):
        """"""
        self.webdav_options = options

        self.client = Client(self.webdav_options)

        self.client.verify = False

        return self.client

    @staticmethod
    def read_config(filename):
        """ """
        with open(filename, 'r') as fp:
            result = json.load(fp)

        return result

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        def parse_bool(x): return str(x).lower() in ['true', '1', 'yes']

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('--upload', default=False, type=parse_bool, nargs='?')
        parser.add_argument('--download', default=False, type=parse_bool, nargs='?')

        parser.add_argument('--config', default=None)

        return parser.parse_args()


def main():
    """메인"""
    args = NextcloudUtils().init_arguments()

    config = NextcloudUtils().read_config(filename=args.config)
    logging.log(MESSAGE, config)

    utils = NextcloudUtils()

    utils.open(options=config['remote']['options'])

    if args.upload is True:
        resp = utils.client.mkdir(config['remote']['path'])
        logging.error({'create remote path': resp, 'config': config})

        utils.client.upload_sync(
            local_path=config['local']['path'],
            remote_path=config['remote']['path'],
        )

    if args.download is True:
        makedirs(config['local']['path'], exist_ok=True)

        utils.client.download_sync(
            local_path=config['local']['path'],
            remote_path=config['remote']['path'],
        )

    return


if __name__ == '__main__':
    main()
