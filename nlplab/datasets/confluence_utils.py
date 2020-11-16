#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import re
from os import makedirs
from os.path import dirname, isdir
from time import sleep
from urllib.parse import urljoin

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup
from tqdm.autonotebook import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    format="[%(levelname)-s] %(message)s",
    handlers=[logging.StreamHandler()],
    level=logging.INFO,
)


class ConfluenceUtils(object):
    """Confluence API 연동 클래스"""

    def __init__(self):
        """생성자"""
        # 참고: https://developer.atlassian.com/server/confluence/confluence-rest-api-examples/

        # 컨플루언스 IP주소 (galadriel)
        self.url = 'http://172.20.93.58:8090'

        # 계정 정보
        self.auth = ('corpus_center', 'test1234')

        # confluence '야구공작소' 공간에 존재하는 페이지ID
        self.state = {
            'request': 14914101,
            'working': 14915832,
            'done': 14915837,
            'page_list': 26744150,
        }

        self.sleep_time = 0.5

    def get_user_info(self, username):
        """사용자 정보를 조회한다. """
        url = '{url}/rest/api/user?username={username}'.format(
            url=self.url,
            username=username
        )

        resp = requests.get(url=url, auth=self.auth, timeout=60, verify=False)
        user_info = resp.json()

        return user_info

    def get_user_group(self, username):
        """그룹 정보를 조회한다. """
        url = '{url}/rest/api/user/memberof?username={username}'.format(
            url=self.url,
            username=username
        )

        resp = requests.get(url=url, auth=self.auth, timeout=60, verify=False)
        user_info = resp.json()

        return user_info

    def get_page_list(self, state):
        """페이지 목록을 조회한다. """
        # 페이지 번호
        url = '{url}/pages/children.action?pageId={page_id}'.format(
            url=self.url,
            page_id=self.state[state]
        )

        resp = requests.get(url=url, auth=self.auth, timeout=60, verify=False)
        page_list = resp.json()

        result = []
        for page in tqdm(page_list, desc='page list: ' + state, dynamic_ncols=True):
            page = self.remove_field(page, ['linkClass', 'position', 'nodeClass', 'href'])
            result.append(page)

            result += self.get_child_page(page_id=page['pageId'])
            sleep(self.sleep_time)

        return result

    def get_child_page(self, page_id):
        """하위 페이지 목록을 조회한다."""
        url = '{url}/rest/api/content/{page_id}/child/page'.format(
            url=self.url,
            page_id=page_id
        )

        resp = requests.get(url=url, auth=self.auth, timeout=60, verify=False)
        page_list = resp.json()

        result = []
        for p in page_list['results']:
            result.append({
                'pageId': p['id'],
                'text': p['title']
            })

        return result

    @staticmethod
    def remove_field(data, field_list):
        """필요 없는 필드 삭제"""
        for field in field_list:
            if field in data:
                del data[field]

        return data

    def get_page(self, page_id):
        """ 하나의 페이지를 읽어 온다. """
        url = '{url}/rest/api/content/{page_id}?expand=body.view,history'.format(
            url=self.url,
            page_id=page_id,
        )

        resp = requests.get(url=url, auth=self.auth, timeout=30, verify=False)
        page = resp.json()

        page['content'] = page['body']['view']['value']
        page['date'] = page['history']['createdDate']

        remove_fields = ['_expandable', '_links', 'body', 'extensions', 'id', 'type', 'status', 'history']
        page = self.remove_field(page, remove_fields)

        return page

    def get_attachment_list(self, page_id):
        """ 첨부 파일 목록을 조회한다. """
        url = '{url}/rest/api/content/{page_id}/child/attachment'.format(
            url=self.url,
            page_id=page_id,
        )

        resp = requests.get(url=url, auth=self.auth, timeout=30, verify=False)
        attach_list = resp.json()

        result = []
        for att in attach_list['results']:
            result.append({
                'name': re.sub(r'\s+', '_', att['title']),
                'url': urljoin(url, att['_links']['download'])
            })

        return result

    def download_all_file(self, page_list, path):
        """전체 첨부파일을 다운로드한다."""
        for page in tqdm(page_list, desc='download', dynamic_ncols=True):
            if 'attachment' not in page:
                continue

            for attach in tqdm(page['attachment'], desc='page: ' + page['pageId'], dynamic_ncols=True):
                self.download(
                    url=attach['url'],
                    filename='{}/{}/{}'.format(path, page['pageId'], attach['name']),
                )

                sleep(self.sleep_time)

        return

    def download(self, filename, url):
        """첨부파일을 다운로드한다."""
        path = dirname(filename)
        if isdir(path) is False:
            makedirs(path)

        # 첨부 파일 다운로드
        with open(filename, 'wb') as fp:
            response = requests.get(url=url, auth=self.auth, timeout=30, verify=False)
            fp.write(response.content)

        return

    def save_all_page(self, page_list, path):
        """전체 페이지를 저장한다."""
        for page in tqdm(page_list, desc='save page', dynamic_ncols=True):
            # 페이지 저장
            if page is not None:
                self.save_page(page=page, path=path)

        return

    @staticmethod
    def save_page(page, path):
        """페이지를 저장한다."""
        import json

        def json_default(value):
            if isinstance(value, pd.DataFrame):
                return value.fillna('').to_records().tolist()

            raise TypeError('not JSON serializable: ' + str(type(value)))

        filename = '{}/{}/{}.json'.format(path, page['pageId'], page['pageId'])

        path = dirname(filename)
        if isdir(path) is False:
            makedirs(path)

        with open(filename, 'wt') as fp:
            line = json.dumps(page, ensure_ascii=False, indent=4, default=json_default) + '\n'
            fp.write(line)

        return

    @staticmethod
    def read_attachment(page_id, path):
        """첨부 파일을 읽는다."""
        from glob import glob
        from os.path import basename

        result = {}
        for filename in tqdm(glob('{}/{}/*.*'.format(path, page_id))):
            if filename.find('.xls') < 0:
                continue

            prefix = basename(filename).replace('.xlsx', '').replace('.xls', '')

            xls = pd.ExcelFile(filename)
            if len(xls.sheet_names) == 1:
                result[prefix] = pd.read_excel(filename)
            else:
                for s_name in xls.sheet_names:
                    result[prefix + '/' + s_name] = pd.read_excel(filename, sheet_name=s_name)

        return result

    @staticmethod
    def to_json(df, filename):
        """파일로 저장한다."""
        df.reset_index().to_json(
            filename,
            force_ascii=False,
            compression='bz2',
            orient='records',
            lines=True,
        )
        return

    @staticmethod
    def read_json(filename):
        """파일로 저장한다."""
        df = pd.read_json(
            filename,
            compression='bz2',
            orient='records',
            lines=True,
        )
        return df

    @staticmethod
    def get_freq_columns(meta_list):
        """빈도가 높은 컬럼 목록을 반환한다."""
        columns = {}
        for meta in meta_list:
            for k in meta.keys():
                if k not in columns:
                    columns[k] = 0
                columns[k] += 1

        return [k for k in columns if columns[k] > 5]

    @staticmethod
    def parse_html(html):
        """선택된 값만 남긴다."""
        # 텍스트 전처리
        html = html.replace(u'\xa0', u'')
        html = html.replace(u'\u3000', u'')

        for tag in ['p', 'div', 'tr', 'td', 'li', 'table']:
            tag = '</{tag}>'.format(tag=tag)
            html = html.replace(tag, tag + '\n')

        for tag in ['ol']:
            tag = '<{tag}>'.format(tag=tag)
            html = html.replace(tag, tag + '\n')

        # 선택형 처리
        soup = BeautifulSoup(html, 'html5lib')
        for tag in soup.find_all('li', {'class': 'checked'}):
            try:
                tag.parent.replace_with(tag.get_text())
            except Exception as e:
                print(e)

        return str(soup)

    @staticmethod
    def get_text(html):
        """본문을 추출한다."""
        soup = BeautifulSoup(html, 'html5lib')
        for tag in soup.find_all('table'):
            tag.extract()

        return re.sub(r'\n+', r'\n', soup.get_text().strip())

    def extract_meta(self, content):
        """메타 정보를 추출한다."""
        html = self.parse_html(content)

        try:
            table_df = pd.read_html(html)
            if len(table_df) == 0:
                return {}

            meta_df = table_df[0]

            if len(table_df) > 1:
                table_df = table_df[1:]
        except Exception as e:
            print(e)
            return {'meta': {}}

        meta_df.fillna('', inplace=True)

        meta = {}
        for i, row in meta_df.iterrows():
            for j in range(0, len(row), 2):
                if row[j] == '' or row[j + 1] == '' or row[j] == row[j + 1]:
                    continue

                k = re.sub(r'\(.+?\)', r'', row[j])
                if k.find('.xls') > 0:
                    continue

                meta[k] = row[j + 1]

        return {
            'meta': meta,
            'table': table_df,
            'content': self.get_text(html),
        }

    def get_all_page(self, page_list):
        """페이지 목록의 전체 내용을 가져온다."""
        meta_list = []
        attach_list = []
        for p in tqdm(page_list, desc='페이지 조회', dynamic_ncols=True):
            page = self.get_page(page_id=p['pageId'])
            p.update(page)

            common = {
                'text': p['text'],
                'date': p['date'],
                'pageId': p['pageId'],
            }

            # 첨부 파일 정보 추출
            p['attachment'] = self.get_attachment_list(page_id=p['pageId'])
            for attach in p['attachment']:
                if attach['name'].find('.xls') < 0:
                    continue

                attach.update(common)
                attach_list.append(attach)

            sleep(self.sleep_time)

            # 메타 정보 추출
            try:
                meta = self.extract_meta(content=page['content'])
                p.update(meta)
            except Exception as e:
                print(e)
                continue

            p['meta'].update(common)
            meta_list.append(p['meta'])

            sleep(self.sleep_time)

        return {
            'page_list': page_list,
            'meta_list': meta_list,
            'attach_list': attach_list,
        }

    def save_report(self, page_info, path):
        """보고서를 저장한다."""
        # 페이지 목록 저장
        page_list_df = pd.DataFrame(
            page_info['page_list'],
            columns=['pageId', 'text', 'date'],
        ).set_index('pageId')

        self.to_json(
            df=page_list_df,
            filename='{}/page_list.json.bz2'.format(path)
        )

        # 메타 정보 저장
        columns = self.get_freq_columns(meta_list=page_info['meta_list'])

        meta_df = pd.DataFrame(
            page_info['meta_list'],
            columns=columns,
        ).set_index('pageId').fillna('')

        self.to_json(
            df=meta_df,
            filename='{}/meta.json.bz2'.format(path)
        )

        # 첨부 파일 정보 저장
        attach_df = pd.DataFrame(page_info['attach_list']).set_index('pageId')

        self.to_json(
            df=attach_df,
            filename='{}/attachment.json.bz2'.format(path)
        )

        return
