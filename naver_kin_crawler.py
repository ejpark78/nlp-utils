#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import sqlite3

from utils import Utils

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)


class NaverKinCrawler(Utils):
    """
    크롤러
    """

    def __init__(self):
        """
        생성자
        """
        super().__init__()

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

    @staticmethod
    def set_pragma(cursor, readonly=True):
        """
        sqlite 의 속도 개선을 위한 설정
        :param cursor: 디비 핸들
        :param readonly: 읽기 전용 플래그
        :return:
        """
        # cursor.execute('PRAGMA threads       = 8;')

        # 700,000 = 1.05G, 2,100,000 = 3G
        cursor.execute('PRAGMA cache_size    = 2100000;')
        cursor.execute('PRAGMA count_changes = OFF;')
        cursor.execute('PRAGMA foreign_keys  = OFF;')
        cursor.execute('PRAGMA journal_mode  = OFF;')
        cursor.execute('PRAGMA legacy_file_format = 1;')
        cursor.execute('PRAGMA locking_mode  = EXCLUSIVE;')
        cursor.execute('PRAGMA page_size     = 4096;')
        cursor.execute('PRAGMA synchronous   = OFF;')
        cursor.execute('PRAGMA temp_store    = MEMORY;')

        if readonly is True:
            cursor.execute('PRAGMA query_only    = 1;')

        return

    def open_detail_db(self, filename, table_name):
        """
        url 을 저장하는 캐쉬 디비(sqlite) 오픈
        :param filename: 파일명
        :param table_name: 테이블명
        :return:
        """
        # 디비 연결
        conn = sqlite3.connect(filename)

        cursor = conn.cursor()

        # 테이블 생성
        if table_name == 'detail':
            sql = '''
              CREATE TABLE IF NOT EXISTS detail (
                d1_id INTEGER NOT NULL,
                dir_id INTEGER NOT NULL,
                doc_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                PRIMARY KEY (d1_id, dir_id, doc_id)
              )
            '''
        elif table_name == 'question_list':
            sql = '''
              CREATE TABLE IF NOT EXISTS question_list (
                d1_id INTEGER NOT NULL,
                dir_id INTEGER NOT NULL,
                doc_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                PRIMARY KEY (d1_id, dir_id, doc_id)
              )
            '''
        else:
            sql = '''
              CREATE TABLE IF NOT EXISTS answer_list (
                d1_id INTEGER NOT NULL,
                dir_id INTEGER NOT NULL,
                doc_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                PRIMARY KEY (d1_id, dir_id, doc_id)
              )
            '''

        cursor.execute(sql)

        # self.set_pragma(cursor, readonly=False)

        # sql 명령 실행
        conn.commit()

        return conn, cursor

    @staticmethod
    def check_doc_id(cursor, d1_id, dir_id, doc_id, table_name):
        """
        다운 받을 문서 아이디가 인덱스 디비에 있는지 검사

        :param cursor: 디비 핸들
        :param d1_id: d1 아이디
        :param dir_id: 카테고리 아이디
        :param doc_id: 문서 아이디
        :param table_name: 테이블명
        :return: 있으면 True, 없으면 False
        """
        # url 주소 조회
        sql = 'SELECT 1 FROM {} WHERE d1_id=? AND dir_id=? AND doc_id=?'.format(table_name)
        cursor.execute(sql, (d1_id, dir_id, doc_id,))

        row = cursor.fetchone()
        if row is not None and len(row) == 1:
            return True

        return False

    @staticmethod
    def save_content(conn, cursor, d1_id, dir_id, doc_id, content, table_name):
        """
        입력 받은 html 저장

        :param conn: 디비 커넥션
        :param cursor: 디비 핸들
        :param d1_id: d1 아이디
        :param dir_id: 카테고리 아이디
        :param doc_id: 문서 아이디
        :param content: 문서 본문
        :param table_name: 테이블명
        :return:
        """
        sql = 'INSERT INTO {} (d1_id, dir_id, doc_id, content) VALUES (?, ?, ?, ?)'.format(table_name)
        try:
            cursor.execute(sql, (d1_id, dir_id, doc_id, content,))
            conn.commit()
        except Exception as e:
            logging.error('디비 저장 오류: {}'.format(e))

        return

    def batch_question_list(self):
        """
        질문 목록 전부를 가져온다.
        """
        data_path = 'data/naver/kin'

        url = 'https://m.kin.naver.com/mobile/qna/kinupList.nhn?' \
              'sortType=writeTime&resultMode=json&dirId={dir_id}&countPerPage={size}&page={page}'

        # dir_id_list = [4, 11, 1, 2, 3, 8, 7, 6, 9, 10, 5, 13, 12, 20]
        dir_id_list = [8, 7, 6, 9, 10, 5, 13, 12, 20]
        for dir_id in dir_id_list:
            result_path = '{data_path}/{dir_id}'.format(data_path=data_path, dir_id=dir_id)

            self.get_question_list(url=url, dir_id=dir_id, result_path=result_path)

        return

    def batch_answer_list(self):
        """
        답변자별 답변 목록 전부를 가져온다.
        """
        result_path = 'data/naver/kin'
        user_filename = 'data/naver/kin/society.user-list'

        answer_list = {}
        with open(user_filename, 'r') as fp:
            for line in fp.readlines():
                line = line.strip()

                if line == '' or line[0] == '#':
                    continue

                user_id, user_name = line.split('\t', maxsplit=1)

                answer_list[user_name] = user_id

        # https://m.kin.naver.com/mobile/user/answerList.nhn?
        #   page=3&countPerPage=20&dirId=0&u=LOLmw2nTPw02cmSW5fzHYaVycqNwxX3QNy3VuztCb6c%3D

        url = 'https://m.kin.naver.com/mobile/user/answerList.nhn?' \
              'page={{page}}&countPerPage={{size}}&dirId={{dir_id}}&u={user_id}'

        for user_name in answer_list:
            user_id = answer_list[user_name]

            query_url = url.format(user_id=user_id)

            print(user_name, user_id, query_url)
            target_path = '{data_path}/by_user/{user_name}'.format(data_path=result_path, user_name=user_name)

            self.get_question_list(url=query_url, dir_id=0, result_path=target_path)

        return

    def get_question_list(self, url, dir_id=4, start=1, end=90000, size=20, result_path='data/naver/kin'):
        """
        네이버 지식인 경제 분야 크롤링

        :param url: 쿼리 조회 URL 패턴
            (https://m.kin.naver.com/mobile/qna/kinupList.nhn?
                sortType=writeTime&resultMode=json&dirId={dir_id}&countPerPage={size}&page={page})
        :param dir_id: 도메인 (4: 경제)
        :param start: 시작 페이지
        :param end: 종료 페이지
        :param size: 페이지 크기
        :param result_path: 결과를 저장할 경로
        :return:
        """
        import json
        import requests
        from time import sleep

        delay = 5

        if not os.path.isdir(result_path):
            os.makedirs(result_path)

        for page in range(start, end):
            file_name = '{result_path}/{page:04d}.json'.format(result_path=result_path, page=page)

            if os.path.exists(file_name):
                logging.info(msg='skip {}'.format(page))
                continue

            query_url = url.format(dir_id=dir_id, size=size, page=page)

            request_result = requests.get(url=query_url, headers=self.headers,
                                          allow_redirects=True, timeout=60)

            result = request_result.json()

            result_list = []
            if 'answerList' in result:
                result_list = result['answerList']

            if 'lists' in result:
                result_list = result['lists']

            if len(result_list) == 0:
                break

            logging.info(msg='{} {:,} {:,}'.format(file_name, page, len(result_list)))
            with open(file_name, 'w') as fp:
                str_lists = json.dumps(result_list, indent=4, ensure_ascii=False)
                fp.write(str_lists)

            sleep(delay)

        return

    def get_detail(self, data_path='data/naver/kin/by_user.economy'):
        """
        상세 페이지 크롤링
        :param data_path:
        :return:
        """
        import json
        import requests

        from time import sleep

        from os import listdir
        from os.path import isdir, isfile, join

        from urllib.parse import urljoin

        from bs4 import BeautifulSoup

        # https://m.kin.naver.com/mobile/qna/detail.nhn?d1id=4&dirId=40308&docId=303328933
        # https://m.kin.naver.com/mobile/qna/detail.nhn?d1Id=6&dirId=60222&docId=301601614

        url = 'https://m.kin.naver.com/mobile/qna/detail.nhn?d1Id={d1Id}&dirId={dirId}&docId={docId}'

        delay = 5

        detail_filename = 'data/naver/detail.sqlite3'
        answer_filename = 'data/naver/answer.sqlite3'

        detail_conn, detail_cursor = self.open_detail_db(filename=detail_filename, table_name='detail')
        answer_conn, answer_cursor = self.open_detail_db(filename=answer_filename, table_name='answer_list')

        history = {}

        batch_answer = []
        batch_detail = []

        for sub_dir in listdir(data_path):
            user_name = sub_dir
            sub_dir = join(data_path, sub_dir)

            if not isdir(sub_dir):
                continue

            for file in listdir(sub_dir):
                file = join(sub_dir, file)
                if not isfile(file):
                    continue

                # 파일 읽기
                with open(file, 'r') as fp:
                    doc_list = json.loads(''.join(fp.readlines()))

                for doc in doc_list:
                    if 'detailUrl' in doc:
                        query_url = urljoin(url, doc['detailUrl'])
                        q, _, _ = self.get_query(url=query_url)
                    else:
                        q = {
                            'd1Id': doc['d1Id'],
                            'dirId': doc['dirId'],
                            'docId': doc['docId']
                        }

                        query_url = url.format(**q)

                    q_id = '{} {} {}'.format(q['d1Id'], q['dirId'], q['docId'])
                    if q_id in history:
                        continue

                    history[q_id] = 1

                    check = self.check_doc_id(d1_id=q['d1Id'], dir_id=q['dirId'], doc_id=q['docId'],
                                              table_name='detail', cursor=detail_cursor)

                    if check is True:
                        logging.info(msg='skip {} {}'.format(q_id, user_name))
                        continue

                    # 질문 상세 페이지 크롤링
                    logging.info(msg='질문 상세: {} {} {}'.format(q_id, user_name, query_url))
                    request_result = requests.get(url=query_url, headers=self.headers,
                                                  allow_redirects=True, timeout=60)

                    # 답변 정보 저장
                    batch_answer.append((q, json.dumps(doc, ensure_ascii=False, sort_keys=True)))

                    if len(batch_answer) > 10:
                        self.batch_save_content(conn=answer_conn, cursor=answer_cursor, table_name='answer_list',
                                                data_list=batch_answer)
                        batch_answer = []

                    # 저장
                    soup = BeautifulSoup(request_result.content, 'html5lib')
                    content_list = soup.findAll('div', {'class': 'sec_col1'})

                    for content in content_list:
                        self.replace_tag(content, ['script', 'javascript', 'style'])
                        value = str(content.prettify())

                        batch_detail.append((q, value))
                        break

                    if len(batch_detail) > 10:
                        self.batch_save_content(conn=detail_conn, cursor=detail_cursor, table_name='detail',
                                                data_list=batch_detail)
                        history = {}
                        batch_detail = []

                    sleep(delay)

        if len(batch_answer) > 0:
            self.batch_save_content(conn=answer_conn, cursor=answer_cursor, table_name='answer_list',
                                    data_list=batch_answer)

        if len(batch_detail) > 0:
            self.batch_save_content(conn=detail_conn, cursor=detail_cursor, table_name='detail',
                                    data_list=batch_detail)

        detail_conn.commit()
        answer_conn.commit()

        detail_conn.close()
        answer_conn.close()

        return

    def batch_save_content(self, conn, cursor, table_name, data_list):
        """
        답변 상세 페이지를 10개 단위로 배치 저장
        :param conn: DB 연결
        :param cursor: DB 커서
        :param table_name: 테이블명
        :param data_list: 저장할 데이터
        :return:
        """
        for item in data_list:
            q, value = item

            self.save_content(conn=conn, cursor=cursor,
                              d1_id=q['d1Id'], dir_id=q['dirId'], doc_id=q['docId'],
                              content=value, table_name=table_name)
        return

    def merge_question(self, data_path='data/naver/kin/4', result_filename='naver-4.xlsx'):
        """
        네이버 지식인 질문 목록 결과 취합
        :param data_path: 질문 목록 경로
        :param result_filename: 결과 파일명
        :return:
        """
        import json

        from os import listdir
        from os.path import isfile, join

        doc_index = {}
        columns = 'fullDirNamePath,docId,title,previewContents,tagList'.split(',')

        for file in listdir(data_path):
            if not isfile(join(data_path, file)):
                continue

            with open('{}/{}'.format(data_path, file), 'r') as fp:
                doc_list = json.loads(''.join(fp.readlines()))

            if len(columns) == 0:
                columns = list(doc_list[0].keys())

            for doc in doc_list:
                path = doc['fullDirNamePath'].replace('Q&A > ', '')
                if path not in doc_index:
                    doc_index[path] = []

                lines = []
                for c in columns:
                    v = doc[c]
                    if v is None:
                        v = ''

                    lines.append('{}'.format(v))

                doc_index[path].append(lines)

        # excel 저장
        self.save_to_excel(file_name=result_filename, data=doc_index, column_names=columns)

        return

    @staticmethod
    def save_to_excel(file_name, data, column_names):
        """
        엑셀로 저장
        :param file_name: 파일명
        :param data: 저장할 데이터
        :param column_names: 컬럼 이름
        :return:
        """
        from openpyxl import Workbook

        status = []

        wb = Workbook()

        for path in data:
            count = '{:,}'.format(len(data[path]))
            status.append([path, count])

            ws = wb.create_sheet(path)

            ws.append(column_names)
            for row in data[path]:
                ws.append(row)

        # 통계 정보 저장
        ws = wb['Sheet']
        for row in status:
            ws.append(row)

        ws.title = 'status'

        wb.save(file_name)

        return

    def parse_content(self, filename):
        """
        상세 정보 HTML 파싱
        :param filename: 디비 파일명
        :return:
        """
        import re
        import sys
        import json
        from bs4 import BeautifulSoup

        table_name = 'detail'

        conn, cursor = self.open_detail_db(filename=filename, table_name=table_name)

        sql = 'SELECT d1_id, dir_id, doc_id, content FROM {}'.format(table_name)
        cursor.execute(sql)

        row_list = cursor.fetchall()[:]

        conn.close()

        # 본문 파싱
        parsing_info = [
            {
                'key': 'category',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': 'depth depth2'}
                }]
            }, {
                'key': 'question',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': 'title_wrapper'}
                }]
            }, {
                'key': 'info',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': '_questionArea'}
                }, {
                    'name': 'div',
                    'attribute': {'class': 'info_zone'}
                }]
            }, {
                'key': 'reply_count',
                'type': 'text',
                'tag': [{
                    'name': 'a',
                    'attribute': {'class': 'reply_count'}
                }, {
                    'name': 'em',
                    'attribute': {'class': 'count_number'}
                }]
            }, {
                'key': 'detail_question',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': '_questionArea'}
                }, {
                    'name': 'div',
                    'attribute': {'class': 'user_content'}
                }]
            }, {
                'key': 'answer',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': '_answer'}
                }, {
                    'name': 'div',
                    'attribute': {'class': 'user_content'}
                }]
            }, {
                'key': 'answer_user',
                'type': 'text',
                'tag': [{
                    'name': 'div',
                    'attribute': {'class': '_answer'}
                }, {
                    'name': 'h3',
                    'attribute': {'class': 'heading'}
                }]
            }, {
                'key': 'user_uid',
                'type': 'data-u',
                'tag': [{
                    'name': 'a',
                    'attribute': {'class': 'button_friend'}
                }]
            }
        ]

        count = 0
        total = len(row_list)

        for row in row_list:
            soup = BeautifulSoup(row[3], 'html5lib')

            qa = {}
            for item in parsing_info:
                tag_list = []
                self.trace_tag(soup=soup, tag_list=item['tag'], i=0, result=tag_list)

                value_list = []
                for tag in tag_list:
                    if item['type'] == 'text':
                        value = tag.get_text().strip().replace('\n', '')
                        value = re.sub('\s+', ' ', value)
                    elif item['type'] == 'html':
                        value = str(tag.prettify())
                    else:
                        if tag.has_attr(item['type']):
                            value = tag[item['type']]
                        else:
                            value = str(tag.prettify())

                    value_list.append(value)

                if len(value_list) == 1:
                    value_list = value_list[0]

                qa[item['key']] = value_list

            qa['question_id'] = '{}-{}-{}'.format(row[0], row[1], row[2])
            print(json.dumps(qa, ensure_ascii=False, sort_keys=True, indent=4), end='\n\n', flush=True)

            count += 1
            print('{:,} / {:,}'.format(count, total), end='\r', flush=True, file=sys.stderr)

        return

    def trace_tag(self, soup, tag_list, i, result):
        """
        :param soup:
        :param tag_list:
        :param result:
        :return:
        """
        from bs4 import element

        if soup is None:
            return

        if len(tag_list) == i and soup is not None:
            result.append(soup)
            return

        soup = soup.findAll(tag_list[i]['name'], attrs=tag_list[i]['attribute'])

        if isinstance(soup, element.ResultSet):
            for tag in soup:
                self.trace_tag(soup=tag, tag_list=tag_list, i=i + 1, result=result)

        return


def init_arguments():
    """
    옵션 설정
    :return:
    """
    import argparse

    parser = argparse.ArgumentParser(description='crawler')

    parser.add_argument('-question_list', help='', action='store_true', default=False)
    parser.add_argument('-answer_list', help='', action='store_true', default=False)
    parser.add_argument('-detail', help='', action='store_true', default=False)

    parser.add_argument('-merge_question', help='', action='store_true', default=False)

    parser.add_argument('-parse_content', help='', action='store_true', default=False)

    parser.add_argument('-filename', help='', default='data/naver/test-detail.sqlite3')

    return parser.parse_args()


if __name__ == '__main__':
    args = init_arguments()

    crawler = NaverKinCrawler()

    if args.question_list:
        crawler.batch_question_list()

    if args.answer_list:
        crawler.batch_answer_list()

    if args.detail:
        crawler.get_detail()

    if args.merge_question:
        crawler.merge_question()

    if args.parse_content:
        crawler.parse_content(filename=args.filename)
