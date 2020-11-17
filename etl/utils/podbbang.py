#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import re
from os import makedirs
from os.path import isdir, isfile

import requests
import sys
import urllib3
from time import sleep
from tqdm import tqdm

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


class PodBbangDL(object):
    """팟빵 mp3 다운로더"""

    def __init__(self):
        """ 생성자 """
        self.args = None
        self.index = set()

    @staticmethod
    def sleep(sec, msg='Sleep'):
        """슬립"""
        if sec <= 0:
            return

        for _ in tqdm(range(sec), desc='{} {} sec.'.format(msg, sec), leave=False):
            sleep(1)

        return

    @staticmethod
    def parse_html_json(content):
        """다운로드 링크를 추출한다."""
        import json

        content = re.sub(r'.+\((\[\{.+\}\]), \'N\'\);.+$', r'\g<1>', content.replace('\n', ''), re.MULTILINE)

        result = json.loads(content)

        return result

    def get_file(self, file_list, data_path):
        """mp3 파일을 다운로드 한다."""
        p_bar = tqdm(file_list)
        for item in p_bar:
            # 파일명&확장자 추출
            ext = item['link_file'].split('.')[-1]

            item['share_title'] = item['share_title'].strip().replace('&quot;', '"').replace('&amp;', '&')
            item['share_title'] = item['share_title'].strip().replace('/', '.')

            f_name = '{}-{}.{}'.format(item['pubdate'], item['share_title'], ext)
            if f_name in self.index:
                continue

            # 기존 파일 확인
            filename = '{}/{}'.format(data_path, f_name)
            if isfile(filename) is True:
                continue

            # 파일 다운로드
            try:
                if p_bar is not None:
                    p_bar.set_description(filename)
            except Exception as e:
                print(e)

            try:
                r = requests.get(item['link_file'])
            except Exception as e:
                logger.error(str(e))
                self.sleep(5)
                continue

            # 파일 저장
            try:
                with open(filename, 'wb') as fp:
                    fp.write(r.content)

                self.index.add(f_name)
            except Exception as e:
                msg = {
                    'url': item['link_file'],
                    'title': item['share_title'],
                    'filename': filename,
                    'exception': str(e),
                }
                logger.error(msg)

            self.sleep(5)

        return

    def trace_download_link(self, c_id, max_page, data_path):
        """다운로드 링크를 추출한다."""
        makedirs(data_path, exist_ok=True)

        base_url = 'http://www.podbbang.com/podbbangchnew/episode_list'

        result = []
        for page in tqdm(range(1, max_page + 1)):
            url = '{}?id={}&page={}&e=&sort=&page_view=&keyword='.format(base_url, c_id, page)

            resp = requests.get(url)
            content = resp.content.decode('utf-8', 'ignore')

            file_list = self.parse_html_json(content=content)

            if len(file_list) == 0:
                break

            result += file_list

            self.sleep(1)

            self.get_file(file_list=file_list, data_path=data_path)
            self.save_index()

        return result

    def read_index(self):
        """"""
        filename = '{}/{}'.format(self.args.data_path, self.args.index)
        if isfile(filename) is False:
            return

        with open(filename, 'r') as fp:
            self.index = set([x.strip() for x in fp.readlines()])

        return

    def save_index(self):
        """ """
        filename = '{}/{}'.format(self.args.data_path, self.args.index)
        with open(filename, 'w') as fp:
            fp.write('\n'.join(list(self.index)))

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--id', default='1770349', help='팟케스트 아이디')
        parser.add_argument('--max_page', default=3, help='최대 페이지')
        parser.add_argument('--data_path', default='data/콩노리', help='다운로드 경로')
        parser.add_argument('--index', default='title.index', help='다운로드 경로')

        return parser.parse_args()


def main():
    """"""
    utils = PodBbangDL()

    utils.args = utils.init_arguments()

    utils.read_index()

    utils.trace_download_link(
        c_id=utils.args.id,
        max_page=int(utils.args.max_page),
        data_path=utils.args.data_path,
    )
    return


if __name__ == '__main__':
    main()
