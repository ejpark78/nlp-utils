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

        self.data_home = 'data/naver/kin'

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        self.detail_parsing_info = [
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

    @staticmethod
    def open_sqlite(filename, table_name):
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
        if table_name == 'user_list':
            sql = '''
              CREATE TABLE IF NOT EXISTS {table_name} (
                u VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                PRIMARY KEY (u)
              )
            '''.format(table_name=table_name)
        else:
            sql = '''
              CREATE TABLE IF NOT EXISTS {table_name} (
                d1_id INTEGER NOT NULL,
                dir_id INTEGER NOT NULL,
                doc_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                PRIMARY KEY (d1_id, dir_id, doc_id)
              )
            '''.format(table_name=table_name)

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
    def save_content(cursor, table_name, values, commit=True, conn=None):
        """
        입력 받은 html 저장

        :param conn: 디비 커넥션
        :param cursor: 디비 핸들
        :param table_name: 테이블명
        :param values: 저장 값 (d1_id, dir_id, doc_id, content,)
        :param commit: 커밋 여부
        :return:
        """
        if table_name == 'user_list':
            sql = 'INSERT INTO {} (u, name, category, content) VALUES (?, ?, ?, ?)'.format(table_name)
        else:
            sql = 'INSERT INTO {} (d1_id, dir_id, doc_id, content) VALUES (?, ?, ?, ?)'.format(table_name)

        try:
            cursor.execute(sql, values)

            if conn is not None and commit is True:
                conn.commit()
        except Exception as e:
            logging.error('디비 저장 오류: {}'.format(e))

        return

    def batch_question_list(self):
        """
        질문 목록 전부를 가져온다.
        """
        url = 'https://m.kin.naver.com/mobile/qna/kinupList.nhn?' \
              'sortType=writeTime&resultMode=json&dirId={dir_id}&countPerPage={size}&page={page}'

        dir_id_list = [4, 11, 1, 2, 3, 8, 7, 6, 9, 10, 5, 13, 12, 20]
        for dir_id in dir_id_list:
            result_path = '{data_path}/{dir_id}'.format(data_path=self.data_home, dir_id=dir_id)

            self.get_question_list(url=url, dir_id=dir_id, result_path=result_path, end=20)

        return

    def batch_answer_list(self, user_filename='society.user-list', result_path='by_user'):
        """
        답변자별 답변 목록 전부를 가져온다.
        :param user_filename: 사용자 목록 파일명
        :param result_path: 저장 경로
        :return:
        """

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
            target_path = '{data_path}/{user_name}'.format(data_path=result_path, user_name=user_name)

            self.get_question_list(url=query_url, dir_id=0, result_path=target_path)

        return

    def get_question_list(self, url, dir_id=4, start=1, end=90000, size=20,
                          result_path='data/naver/kin'):
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

    def get_elite_user_list(self):
        """
        명예의 전당 채택과 년도별 사용자 목록 추출
        :return:
        """
        import json
        import requests
        from time import sleep

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        month = 0
        for year in range(2012, 2019):
            url = 'https://kin.naver.com/hall/eliteUser.nhn?year={}'.format(year)

            result = requests.get(url=url, headers=headers,
                                  allow_redirects=True, timeout=30, verify=False)

            cookies = requests.utils.dict_from_cookiejar(result.cookies)
            logging.info(msg='eliteUser cookie: {} {}'.format(result, cookies))

            headers['referer'] = url

            filename = '{}/users/elite_user_list.{}.json'.format(self.data_home, year)

            for page in range(1, 6):
                list_url = 'https://kin.naver.com/ajax/eliteUserAjax.nhn?year={}&month={}&page={}'.format(year, month,
                                                                                                          page)

                request_result = requests.get(url=list_url, headers=headers, cookies=cookies,
                                              allow_redirects=True, timeout=60)

                result = request_result.json()

                if 'eliteUserList' in result:
                    logging.info(msg='{}, {}'.format(len(result['eliteUserList']), list_url))

                    with open(filename, 'a') as fp:
                        for user in result['eliteUserList']:
                            str_line = json.dumps(user, ensure_ascii=False, sort_keys=True, indent=4)
                            fp.write(str_line + '\n\n')
                            fp.flush()

                sleep(5)

        return

    def get_expert_user_list(self):
        """
        분야별 전문가 목록 추출
        :return:
        """
        import json
        import requests
        from time import sleep

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        category_list = {
            '금융': '401',
            '예금, 적금': '40101',
            '주식, 증권': '40102',
            '보험': '40103',
            '신용카드': '40104',
            '대출': '40105',
            '개인 신용, 회복': '40106',
            '뱅킹, 금융업무': '40107',
            '가상화폐': '40108',
            '부동산': '402',
            '매매': '40201',
            '임대차': '40202',
            '분양, 청약': '40203',
            '경매': '40204',
            '세금, 세무': '403',
            '소득세': '40301',
            '법인세': '40302',
            '상속세, 증여세': '40303',
            '부가가치세': '40304',
            '종합부동산세': '40305',
            '취득세, 등록세': '40306',
            '재산세': '40307',
            '자동차세': '40308',
            '세금 정책, 제도': '40309',
            '관세': '40310',
            '연말정산': '40311',
            '경영': '404',
            '마케팅, 영업': '40401',
            '회계, 감사, 재무 관리': '40402',
            '인사, 조직 관리': '40403',
            '연구개발, 생산, 물류': '40404',
            '경영정보시스템': '40405',
            '무역': '405',
            '수출': '40501',
            '수입': '40502',
            '직업, 취업': '406',
            '공무원': '40601',
            '교육, 연구, 학문': '40602',
            '의료, 법률, 금융': '40603',
            '복지, 종교': '40604',
            '문화, 예술': '40605',
            '관광, 요식업, 스포츠': '40606',
            '유통, 판매, 영업': '40607',
            '컴퓨터, 프로그래밍': '40608',
            '생산, 기술': '40609',
            '사무지원': '40610',
            '아르바이트': '40611',
            '취업 정책, 제도': '40612',
            '구인구직사이트': '40613',
            '창업': '407',
            '판매, 유통업': '40701',
            '관광, 요식업': '40702',
            '서비스업': '40703',
            '창업성장': '40704',
            '경제 정책, 제도': '408',
            '경제 동향, 이론': '409',
            '경제 기관, 단체': '410',
        }

        url_frame = 'https://kin.naver.com/qna/directoryExpertList.nhn?dirId={dir_id}'
        list_url_frame = [
            'https://kin.naver.com/ajax/qnaWeekRankAjax.nhn?requestId=weekRank&dirId={dir_id}&page={page}',
            'https://kin.naver.com/ajax/qnaTotalRankAjax.nhn?requestId=totalRank&dirId={dir_id}&page={page}'
        ]

        for dir_name in category_list:
            dir_id = category_list[dir_name]
            url = url_frame.format(dir_id=dir_id)

            result = requests.get(url=url, headers=headers,
                                  allow_redirects=True, timeout=30, verify=False)

            cookies = requests.utils.dict_from_cookiejar(result.cookies)
            logging.info(msg='cookie: {} {}'.format(result, cookies))

            headers['referer'] = url

            filename = '{}/users/expert/{}.json'.format(self.data_home, dir_name)

            for u_frame in list_url_frame:
                for page in range(1, 10):
                    list_url = u_frame.format(dir_id=dir_id, page=page)

                    request_result = requests.get(url=list_url, headers=headers, cookies=cookies,
                                                  allow_redirects=True, timeout=60)

                    result = request_result.json()

                    if 'result' in result:
                        logging.info(msg='{}, {}'.format(len(result['result']), list_url))

                        with open(filename, 'a') as fp:
                            for user in result['result']:
                                str_line = json.dumps(user, ensure_ascii=False, sort_keys=True, indent=4)
                                fp.write(str_line + '\n\n')
                                fp.flush()

                        if len(result['result']) != 20:
                            break

                    sleep(5)

        return

    def get_detail(self, data_path='by_user.economy'):
        """
        상세 페이지 크롤링
        :param data_path: 데이터 경로
        :return:
            def _remove_attrs(soup):
                for tag in soup.findAll(True):
                    tag.attrs = None
                return soup

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

        detail_conn, detail_cursor = self.open_sqlite(filename=detail_filename, table_name='detail')
        answer_conn, answer_cursor = self.open_sqlite(filename=answer_filename, table_name='answer_list')

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
                    str_doc = json.dumps(doc, ensure_ascii=False, sort_keys=True)

                    values = (q['d1Id'], q['dirId'], q['docId'], str_doc,)
                    batch_answer.append(values)

                    if len(batch_answer) > 10:
                        self.batch_save_content(cursor=answer_cursor, table_name='answer_list',
                                                value_list=batch_answer)

                        answer_conn.commit()
                        batch_answer = []

                    # 저장
                    soup = BeautifulSoup(request_result.content, 'html5lib')
                    content_list = soup.findAll('div', {'class': 'sec_col1'})

                    for content in content_list:
                        self.replace_tag(content, ['script', 'javascript', 'style'])

                        # 필요없는 테그 삭제
                        tag_list = content.findAll('div', {'id': 'suicidalPreventionBanner'})
                        for remove_tag in tag_list:
                            remove_tag.extract()

                        value = str(content.prettify())

                        values = (q['d1Id'], q['dirId'], q['docId'], value,)
                        batch_detail.append(values)
                        break

                    if len(batch_detail) > 10:
                        self.batch_save_content(cursor=detail_cursor, table_name='detail',
                                                value_list=batch_detail)

                        detail_conn.commit()

                        history = {}
                        batch_detail = []

                    sleep(delay)

        if len(batch_answer) > 0:
            self.batch_save_content(cursor=answer_cursor, table_name='answer_list',
                                    value_list=batch_answer)
            answer_conn.commit()

        if len(batch_detail) > 0:
            self.batch_save_content(cursor=detail_cursor, table_name='detail',
                                    value_list=batch_detail)
            detail_conn.commit()

        detail_conn.close()
        answer_conn.close()

        return

    def batch_save_content(self, cursor, table_name, value_list):
        """
        답변 상세 페이지를 10개 단위로 배치 저장
        :param cursor: DB 커서
        :param table_name: 테이블명
        :param value_list: 저장할 데이터
        :return:
        """
        for values in value_list:
            self.save_content(cursor=cursor, table_name=table_name,
                              values=values, commit=False, conn=None)

        return

    def merge_question(self, data_path='detail.json.bz2', result_filename='detail.xlsx'):
        """
        네이버 지식인 질문 목록 결과 취합
        :param data_path: 질문 목록 경로
        :param result_filename: 결과 파일명
        :return:
        """
        import bz2
        import sys
        import json

        from os import listdir
        from os.path import isdir, join

        # 파일 목록 추출
        file_list = []
        if isdir(data_path):
            for file in listdir(data_path):
                filename = join(data_path, file)
                if isdir(filename):
                    continue

                file_list.append(filename)

            file_list = sorted(file_list)
        else:
            file_list = [data_path]

        doc_index = {}

        # columns = []
        columns = 'fullDirNamePath,docId,title,previewContents,tagList'.split(',')

        count = 0
        for file in file_list:
            doc_list = []
            if file.find('.bz2') > 0:
                with bz2.open(file, 'rb') as fp:
                    buf = []
                    for line in fp.readlines():
                        line = str(line, encoding='utf-8').strip()

                        buf.append(line)

                        if len(buf) > 0 and line == '}':
                            body = ''.join(buf)
                            doc_list.append(json.loads(body))

                            buf = []
            else:
                with open(file, 'r') as fp:
                    doc_list = json.loads(''.join(fp.readlines()))

            for doc in doc_list:
                path = 'etc'
                if 'fullDirNamePath' in doc:
                    path = doc['fullDirNamePath'].replace('Q&A > ', '')

                if 'category' in doc:
                    path = doc['category']

                if isinstance(path, list):
                    path = 'etc'

                if path not in doc_index:
                    doc_index[path] = []

                doc_index[path].append(doc)

                line = json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=4)
                print(line, end='\n\n', flush=True)

                count += 1
                print('{} {:,}'.format(file, count), end='\r', flush=True, file=sys.stderr)

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

            if len(column_names) == 0:
                column_names = list(data[path][0].keys())

            ws.append(column_names)
            for doc in data[path]:
                lines = []
                for c in column_names:
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

        conn, cursor = self.open_sqlite(filename=filename, table_name=table_name)

        sql = 'SELECT d1_id, dir_id, doc_id, content FROM {}'.format(table_name)
        cursor.execute(sql)

        row_list = cursor.fetchall()[:]

        conn.close()

        # 본문 파싱
        count = 0
        total = len(row_list)

        for row in row_list:
            soup = BeautifulSoup(row[3], 'html5lib')

            qa = {}
            for item in self.detail_parsing_info:
                tag_list = []
                self.trace_tag(soup=soup, tag_list=item['tag'], index=0, result=tag_list)

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
            line = json.dumps(qa, ensure_ascii=False, sort_keys=True, indent=4)
            print(line, end='\n\n', flush=True)

            count += 1
            print('{:,} / {:,}'.format(count, total), end='\r', flush=True, file=sys.stderr)

        return

    def trace_tag(self, soup, tag_list, index, result):
        """
        :param soup: bs4 개체
        :param tag_list: 테그 위치 목록
        :param index: 테그 인덱스
        :param result: 결과
        :return:
        """
        from bs4 import element

        if soup is None:
            return

        if len(tag_list) == index and soup is not None:
            result.append(soup)
            return

        soup = soup.findAll(tag_list[index]['name'],
                            attrs=tag_list[index]['attribute'])

        if isinstance(soup, element.ResultSet):
            for tag in soup:
                self.trace_tag(soup=tag, tag_list=tag_list, index=index + 1, result=result)

        return

    def insert_user_list(self, data_path='', category=''):
        """
        사용자 목록을 sqlite3 에 입력
        :param data_path: 사용자 목록이 저장된 경로
        :param category: 카테고리 정보

        expert 사용자 정보 (랭킹)
            {
                "encodedU": "qXbgNEA8MzxTqYTJ0KdlLcw9j%2FOdLGczxe1xmpkrRuQ%3D",
                "lastWeekRank": 3,
                "nickname": "",
                "photoUrl": "https://ssl.pstatic.net/static/kin/09renewal/avatar/33x33/8.png",
                "totalDirPoint": 383,
                "u": "qXbgNEA8MzxTqYTJ0KdlLcw9j/OdLGczxe1xmpkrRuQ=",
                "useNickname": false,
                "userId": "ospdb",
                "viewUserId": "ospd****",
                "weekDirPoint": 101,
                "weekRank": 2
            }

        elite 년도별 전문가
            {
                "activeDirId": 10102,
                "activeDirName": "노트북",
                "cheerCnt": 39,
                "cheered": false,
                "description": "전자제품 박학다식 끝판왕",
                "displayYn": "Y",
                "eliteFlag": 0,
                "honorKin": false,
                "month": 5,
                "powerKin": false,
                "profilePhotoUrl": "https://kin-phinf.pstatic.net/20180426_110/1524732986074Gv6GP_JPEG/%BA%CE%C7%B0%C1%A4%B8%AE.jpg?type=w200",
                "selectBestCnt": 2997,
                "u": "X/XrUkwNpssPPgqPB+TNUGm+PjMq/YHPNL4nAHhrM74=",
                "viewId": "박학다식전문가",
                "year": 2018
            }

        분야별 지식인
            GyOWWwK059X2dLySrX%2Fd6uWqE60LWxo1q2tZ9d5IOc8%3D	우리세무사
            JikckmNyrpnFIST1cyw44Nbizfuto0Tb0LrSrUSgILw%3D	깊은샘

        :return:
        """
        import re
        import json

        from os import listdir
        from os.path import isdir, join

        from urllib.parse import unquote

        # 파일 로딩
        user_list = []
        if isdir(data_path):
            for file in listdir(data_path):
                print(file)

                filename = join(data_path, file)
                if isdir(filename):
                    continue

                with open(filename, 'r') as fp:
                    buf = []
                    for line in fp.readlines():
                        line = line.rstrip()

                        buf.append(line)

                        if line != '}':
                            continue

                        doc = json.loads(''.join(buf))
                        buf = []

                        doc['f_name'] = re.sub('^.+/(.+?)\.json', '\g<1>', filename)
                        user_list.append(doc)
        else:
            with open(data_path, 'r') as fp:
                f_name = re.sub('^.+/(.+?)$', '\g<1>', data_path)

                for line in fp.readlines():
                    line = line.rstrip()
                    if line == '' or line[0] == '#':
                        continue

                    u, name = line.split('\t', maxsplit=1)

                    user_list.append({
                        'u': unquote(u),
                        'viewId': name,
                        'f_name': f_name
                    })

        db_filename = 'data/naver/kin/user_list.sqlite3'
        table_name = 'user_list'

        conn, cursor = self.open_sqlite(filename=db_filename, table_name=table_name)

        value_list = []

        for user in user_list:
            name = ''
            if 'userId' in user:
                name = user['userId']

            if 'viewId' in user:
                name = user['viewId']

            print(name, user['u'])

            # (u, name, category, content)
            str_user = json.dumps(user, ensure_ascii=False, sort_keys=True, indent=4)
            values = (user['u'], name, '{} ({})'.format(category, user['f_name']), str_user,)
            value_list.append(values)

            if len(value_list) > 100:
                self.batch_save_content(cursor=cursor, table_name=table_name,
                                        value_list=value_list)
                conn.commit()

                value_list = []

        if len(value_list) > 0:
            self.batch_save_content(cursor=cursor, table_name=table_name,
                                    value_list=value_list)
            conn.commit()

        conn.close()

        return

    def insert_question_list(self, data_path=''):
        """
        질문 목록을 sqlite3 에 입력
        :param data_path: 사용자 목록이 저장된 경로 data/naver/kin/question_list/경제

        질문 자료 구조
            {
                "thumbnailInfos": null,
                "betPoint": 0,
                "kinupPoint": 0,
                "d2id": 701,
                "readCnt": 1,
                "isContainsLocation": false,
                "d1Id": 7,
                "title": "명치아플땐?",
                "qboardId": 0,
                "answerCnt": 1,
                "writeTime": 1529107180000,
                "isFromMobile": true,
                "firstFlag": null,
                "mediaFlag": 0,
                "isAutoTitle": true,
                "kinupCnt": 0,
                "isAdult": false,
                "fullDirNamePath": "Q&A > 건강 > 건강상담 > 내과 > 소화기내과",
                "autoTitle": false,
                "renewFlag": null,
                "gdId": "10000009_00001218bc79",
                "tags": null,
                "d5id": 0,
                "unreadFlag": null,
                "entryLink": null,
                "answerTime": null,
                "adultFlag": "N",
                "inputDevice": "MOBILE_WEB",
                "dirName": "소화기내과",
                "kinFlag": null,
                "isContainsAudio": false,
                "dirId": 7010102,
                "juniorFlag": null,
                "isContainsMovie": false,
                "isContainsImage": false,
                "previewContents": "명치아플땐?",
                "entry": null,
                "d4id": 7010102,
                "tagList": null,
                "docId": 303611001,
                "formattedWriteTime": "오늘",
                "metooWonderCnt": 0,
                "d3id": 70101,
                "openFlag": "N"
            }

        :return:
        """
        import json

        from os import listdir
        from os.path import isdir, join

        # 파일 로딩
        count = 0
        question_list = {}
        for file in listdir(data_path):
            filename = join(data_path, file)
            if isdir(filename):
                continue

            logging.info(msg='filename: {}'.format(filename))

            # 질문 로딩
            with open(filename, 'r') as fp:
                body = '\n'.join(fp.readlines())

                q_list = json.loads(body)

                # 카테고리별로 분리
                for q in q_list:
                    category_id = '{}'.format(q['dirId'])

                    if category_id not in question_list:
                        question_list[category_id] = []

                    count += 1
                    question_list[category_id].append(q)

        logging.info(msg='question_list: category={:,}, total={:,}'.format(len(question_list), count))

        table_name = 'question_list'

        for category_id in question_list:
            db_filename = 'data/naver/kin/question_list/{}.sqlite3'.format(category_id)
            conn, cursor = self.open_sqlite(filename=db_filename, table_name=table_name)

            value_list = []
            for question in question_list[category_id]:
                # (d1_id, dir_id, doc_id, category, content)
                content = json.dumps(question, ensure_ascii=False, sort_keys=True, indent=4)
                values = (question['d1Id'], question['dirId'], question['docId'], content,)
                value_list.append(values)

                if len(value_list) > 500:
                    self.batch_save_content(cursor=cursor, table_name=table_name,
                                            value_list=value_list)
                    conn.commit()

                    value_list = []

            if len(value_list) > 0:
                self.batch_save_content(cursor=cursor, table_name=table_name,
                                        value_list=value_list)
                conn.commit()

            conn.close()

        return


def init_arguments():
    """
    옵션 설정
    :return:
    """
    import textwrap
    import argparse

    description = textwrap.dedent('''\
# 질문 목록 크롤링
python3 naver_kin_crawler.py -question

# 답변 목록 크롤링 
python3 naver_kin_crawler.py -answer_list \\
    -filename data/naver/kin/users/의료 \\
    -result_path data/naver/kin/by_user.의료
    
python3 naver_kin_crawler.py -answer_list \\
    -filename data/naver/kin/users/분야별지식인 \\
    -result_path data/naver/kin/by_user.분야별지식인

python3 naver_kin_crawler.py -answer_list \\
    -filename data/naver/kin/users/economy.partner \\
    -result_path data/naver/kin/by_user.economy
    
python3 naver_kin_crawler.py -answer_list \\
    -filename data/naver/kin/users/society.partner \\
    -result_path data/naver/kin/by_user.society

# 질문 상세 페이지 크롤링 
python3 naver_kin_crawler.py -detail -data_path data/naver/kin/by_user.economy
python3 naver_kin_crawler.py -detail -data_path data/naver/kin/by_user.society
python3 naver_kin_crawler.py -detail -data_path data/naver/kin/question_list

# 질문 상세 취합
python3 naver_kin_crawler.py -parse_content -filename data/naver/test-detail.sqlite3

# 질문 목록 취합
python3 naver_kin_crawler.py -merge_question \\
    -data_path data/naver/kin/question_list/경제 \\
    -filename data/naver/kin/question_list.economy.xlsx \\
    | bzip2 - > data/naver/kin/question_list.economy.json.bz2

# 질문 목록 취합
IFS=$'\\n'
for d in $(ls -1 data/naver/kin/question_list) ; do
    echo ${d}

    python3 naver_kin_crawler.py -merge_question \\
        -data_path data/naver/kin/question_list/${d} \\
        -filename data/naver/kin/${d}.xlsx \\
        | bzip2 - > data/naver/kin/${d}.json.bz2
done

# 사용자 목록을 DB에 저장
python3 naver_kin_crawler.py -insert_user_list -data_path data/naver/kin/users/partner/economy -category '경제 지식파트너'
python3 naver_kin_crawler.py -insert_user_list -data_path data/naver/kin/users/partner/society -category '사회 지식파트너'
python3 naver_kin_crawler.py -insert_user_list -data_path data/naver/kin/users/expert -category 경제
python3 naver_kin_crawler.py -insert_user_list -data_path data/naver/kin/users/elite -category 년도별

# 질문 목록을 DB에 저장
python3 naver_kin_crawler.py -insert_question_list -data_path data/naver/kin/question_list/경제

IFS=$'\\n'
for d in $(ls -1 data/naver/kin/question_list.old) ; do
    echo ${d}

    python3 naver_kin_crawler.py -insert_question_list \\
        -data_path data/naver/kin/question_list.old/${d}
done


    ''')

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=description)

    # 크롤링
    parser.add_argument('-question_list', action='store_true', default=False,
                        help='질문 목록 크롤링')

    parser.add_argument('-elite_user_list', action='store_true', default=False,
                        help='전문가 목록 크롤링')
    parser.add_argument('-expert_user_list', action='store_true', default=False,
                        help='랭킹 사용자 목록 크롤링')
    parser.add_argument('-answer_list', action='store_true', default=False,
                        help='답변 목록 크롤링 (전문가 답변, 지식 파트너 답변 등)')
    parser.add_argument('-detail', action='store_true', default=False,
                        help='답변 상세 페이지 크롤링')

    # 결과 취합
    parser.add_argument('-merge_question', action='store_true', default=False,
                        help='질문 목록을 엑셀로 저장')
    parser.add_argument('-parse_content', action='store_true', default=False,
                        help='질문 상세 페이지에서 정보 추출')
    parser.add_argument('-insert_user_list', action='store_true', default=False,
                        help='사용자 목록을 DB에 저장')
    parser.add_argument('-insert_question_list', action='store_true', default=False,
                        help='질문 목록을 DB에 저장')

    # 파라메터
    parser.add_argument('-filename', default='data/naver/test-detail.sqlite3', help='')
    parser.add_argument('-result_path', default='data/naver/kin', help='')
    parser.add_argument('-data_path', default='data/naver/kin', help='')
    parser.add_argument('-category', default='', help='')

    return parser.parse_args()


if __name__ == '__main__':
    args = init_arguments()

    crawler = NaverKinCrawler()

    if args.question_list:
        crawler.batch_question_list()

    if args.answer_list:
        crawler.batch_answer_list(user_filename=args.filename, result_path=args.result_path)

    if args.detail:
        crawler.get_detail(data_path=args.data_path)

    if args.merge_question:
        crawler.merge_question(data_path=args.data_path, result_filename=args.filename)

    if args.parse_content:
        crawler.parse_content(filename=args.filename)

    if args.elite_user_list:
        crawler.get_elite_user_list()

    if args.expert_user_list:
        crawler.get_expert_user_list()

    if args.insert_user_list:
        crawler.insert_user_list(data_path=args.data_path, category=args.category)

    if args.insert_question_list:
        crawler.insert_question_list(data_path=args.data_path)
