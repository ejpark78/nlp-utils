#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


class CorpusLibraryUtils(object):
    """코퍼스 처리 클리스"""

    def __init__(self):
        """생성자"""
        self.webdav_home = '코퍼스 취합'

        self.webdav_options = {
            'webdav_hostname': 'https://corpus.ncsoft.com:8080/remote.php/webdav/',
            'webdav_login': 'corpus_center',
            'webdav_password': 'nlplab2018'
        }

    def open_webdev_client(self):
        """"""
        import webdav.client as wc

        client = wc.Client(self.webdav_options)

        client.default_options.update({
            'SSL_VERIFYPEER': 0,
            'SSL_VERIFYHOST': 0
        })

        return client

    def get_cloud_corpus_tree(self):
        """클라우드 코퍼스 트리 구조 반환 """
        client = self.open_webdev_client()

        result = {}

        files_list = client.list(self.webdav_home)

        for file in files_list[1:]:
            if 'xlsx' in file:
                continue

            file = file.replace('/', '')

            sub_list = client.list('{}/{}'.format(self.webdav_home, file))

            for sub_file in sub_list[1:]:
                # 마지막 / 제거
                sub_file = sub_file.replace('/', '')

                if file not in result:
                    result[file] = []

                result[file].append(sub_file)

        return result

    def get_cloud_corpus_list(self):
        """클라우드 코퍼스 목록 반환, 페이지 목록 반환"""
        client = self.open_webdev_client()

        result = []

        files_list = client.list(self.webdav_home)

        for file in files_list[1:]:
            if 'xlsx' in file:
                continue

            file = file.replace('/', '')

            result.append(file)

        return result

    def get_cloud_corpus_sublist(self, name, page, size):
        """코퍼스 하위 목록 조회 """
        client = self.open_webdev_client()

        result = []

        home_path = '{}/{}'.format(self.webdav_home, name)
        files_list = client.list(home_path)
        if files_list[0][:-1] == name:
            files_list = files_list[1:]

        # size 만큼 자르기
        start_pos = (page - 1) * size

        for file in files_list[start_pos:start_pos + size]:
            if 'xlsx' in file:
                continue

            file = file.replace('/', '')

            result.append(file)

        return result

    def get_cloud_corpus_sub_item(self, group, corpus_name):
        """해당 코퍼스 디렉토리에 포함된 파일들을 불러와 저장 """
        import os
        import json

        client = self.open_webdev_client()

        home_path = '{}/{}/{}'.format(self.webdav_home, group, corpus_name)
        local_home = os.getenv('LOCAL_HOME_PATH', '/tmp')
        files_list = client.list(home_path)
        if local_home == 'null':
            local_home = ''

        result = {}
        for file in files_list:
            column = ''

            flag = False
            for needle in ['README.json', 'sample.json']:
                if file.find(needle) == -1:
                    continue

                flag = True
                column = needle.replace('.json', '')
                break

            if flag is not True:
                continue

            remote_path = '{}/{}'.format(home_path, file)
            if local_home == '':
                local_path = remote_path.replace('/', '.')
            else:
                local_path = '{}/{}'.format(local_home, remote_path.replace('/', '.'))

            if os.path.exists(local_path) is False:
                self.download_file(client=client, remote_file=remote_path, local_path=local_path)

            if os.path.exists(local_path) is False:
                continue

            with open(local_path, 'rb') as fp:
                value_list = []
                buf = ''
                for line in fp.readlines():
                    line = str(line.rstrip(), 'utf-8')
                    if line == '':
                        continue

                    buf += line

                    if line == '}':
                        value = json.loads(buf)
                        value_list.append(value)

                        buf = ''

                if buf != '':
                    value = json.loads(buf)
                else:
                    value = value_list

                if column == 'README':
                    result[column] = value
                else:
                    if column not in result:
                        result[column] = {}

                    result[column][file] = value

        return result

    @staticmethod
    def download_file(client, remote_file, local_path):
        """파일을 다운로드한다."""
        import pycurl
        from webdav.urn import Urn
        from webdav.exceptions import NotConnection

        try:
            urn = Urn(remote_file)

            with open(local_path, 'wb') as local_file:

                url = {
                    'hostname': client.webdav.hostname,
                    'root': client.webdav.root,
                    'path': urn.quote()
                }

                options = {
                    'URL': "{hostname}{root}{path}".format(**url),
                    'HTTPHEADER': client.get_header('download_file'),
                    'WRITEDATA': local_file,
                    'NOPROGRESS': 0,
                    'NOBODY': 0
                }

                request = client.Request(options=options)

                request.perform()
                request.close()

        except pycurl.error:
            raise NotConnection(client.webdav.hostname)
