#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sqlite3

from utils import Utils

logging.basicConfig(format="[%(levelname)-s] %(message)s",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)


class SqliteUtils(Utils):
    """ sqlite 유틸 """

    def __init__(self):
        """ 생성자 """
        super().__init__()

    @staticmethod
    def set_pragma(cursor, readonly=True):
        """ sqlite 속도 개선을 위한 설정

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
        """url 을 저장하는 캐쉬 디비(sqlite)를 오픈한다.

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
        """다운 받을 문서 아이디가 인덱스 디비에 있는지 검사한다.

        :param cursor: 디비 핸들
        :param d1_id: d1 아이디
        :param dir_id: 카테고리 아이디
        :param doc_id: 문서 아이디
        :param table_name: 테이블명
        :return: 있으면 True, 없으면 False
        """
        # url 주소 조회
        sql = 'SELECT 1 ' \
              'FROM {} ' \
              'WHERE d1_id=? AND dir_id=? AND doc_id=?'.format(table_name)
        cursor.execute(sql, (d1_id, dir_id, doc_id,))

        row = cursor.fetchone()
        if row is not None and len(row) == 1:
            return True

        return False

    @staticmethod
    def save_content(cursor, table_name, values, update=False, commit=True, conn=None):
        """ 입력 받은 html 를 저장한다.

        :param conn: 디비 커넥션
        :param cursor: 디비 핸들
        :param table_name: 테이블명
        :param values: 저장 값 (d1_id, dir_id, doc_id, content,)
        :param commit: 커밋 여부
        :param update: 업데이트 여부
        :return:
        """
        if table_name == 'user_list':
            sql = 'INSERT INTO {} (u, name, category, content) ' \
                  'VALUES (?, ?, ?, ?)'.format(table_name)
        else:
            sql = 'INSERT INTO {} (d1_id, dir_id, doc_id, content) ' \
                  'VALUES (?, ?, ?, ?)'.format(table_name)

        try:
            cursor.execute(sql, values)
        except sqlite3.IntegrityError as e:
            if update is True:
                if table_name == 'user_list':
                    pass
                else:
                    update_values = (values[3], values[0], values[1], values[2],)

                    sql = 'UPDATE {} SET content=? WHERE d1_id=? AND dir_id=? AND doc_id=?'.format(table_name)
                    try:
                        cursor.execute(sql, update_values)
                        logging.info('디비 내용 업데이트: {}-{}'.format(values[1], values[2]))
                    except Exception as e:
                        logging.error('디비 업데이트 오류: {}'.format(e))
            else:
                logging.error('키 중복: {}'.format(e))
        except Exception as e:
            logging.error('디비 저장 오류: {}'.format(e))

        try:
            if conn is not None and commit is True:
                conn.commit()
        except Exception as e:
            logging.error('디비 커밋 오류: {}'.format(e))

        return


class NaverKinUtils(SqliteUtils):
    """ 네이버 크롤링 결과 저장 유틸 """

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.data_home = 'data/naver/kin'

        self.elastic_info = {
            'host': 'http://koala:9200',
            'index': 'naver_kin',
            'type': 'naver_kin',
            'insert': True
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

        self.category_list = {
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

    def save_data_list(self, data_list, result_path,
                       table_name='question_list', update=False):
        """ 질문 목록을 저장한다.

        :param data_list: 데이터 목록
        :param result_path: 저장 경로
        :param update: 내용 업데이트 플래그
        :param table_name: 테이블명
        :return:
        """
        import os

        # 결과 경로가 없는 경우 생성
        if not os.path.exists(result_path):
            os.makedirs(result_path)

        for dir_id in data_list:
            db_filename = '{}/{}.sqlite3'.format(result_path, dir_id)
            conn, cursor = self.open_sqlite(filename=db_filename, table_name=table_name)

            buf = []
            for value in data_list[dir_id]:
                buf.append(value)

                if len(buf) > 500:
                    self.batch_save_content(cursor=cursor, table_name=table_name,
                                            value_list=buf, update=update)
                    conn.commit()
                    buf = []

            if len(buf) > 0:
                self.batch_save_content(cursor=cursor, table_name=table_name,
                                        value_list=buf, update=update)
                conn.commit()

            conn.close()

        return

    def batch_save_content(self, cursor, table_name, value_list, update=False):
        """ 답변 상세 페이지를 10개 단위로 배치 단위로 저장한다.

        :param cursor: DB 커서
        :param table_name: 테이블명
        :param value_list: 저장할 데이터
        :param update: 데이터 갱신 여부
        :return:
        """
        for values in value_list:
            self.save_content(cursor=cursor, table_name=table_name, update=update,
                              values=values, commit=False, conn=None)

        return

    @staticmethod
    def save_to_excel(file_name, data, column_names):
        """ 크롤링 결과를 엑셀로 저장한다.

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

    def insert_question_list(self, data_path=''):
        """ 질문 목록을 elastic-search 에 저장한다.

        :param data_path:
            사용자 목록이 저장된 경로 data/naver/kin/question_list/경제

        질문 자료 구조::

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
        import shutil

        from os import listdir
        from os.path import isdir, join

        table_name = 'question_list'

        # 인덱스명 설정
        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = table_name

        bulk_size = 1000

        # 파일 로딩
        count = 0
        question_list = {}
        for file in listdir(data_path):
            filename = join(data_path, file)
            if isdir(filename):
                continue

            logging.info(msg='filename: {}'.format(filename))

            # sqlite all data fetch
            conn, cursor = self.open_sqlite(filename=filename, table_name=table_name)

            sql = 'SELECT * FROM {}'.format(table_name)
            cursor.execute(sql)

            # columns = [d[0] for d in cursor.description]
            for row in cursor.fetchall():
                doc = json.loads(row[3])

                doc['_id'] = '{}-{}-{}'.format(row[0], row[1], row[2])

                self.save_elastic(document=doc, elastic_info=self.elastic_info,
                                  db_name=table_name, insert=True, bulk_size=bulk_size)

            self.save_elastic(document=None, elastic_info=self.elastic_info,
                              db_name=table_name, insert=True, bulk_size=0)

            conn.close()

            # 완료 파일 이동
            shutil.move(filename, '{}/done/{}'.format(data_path, file))

        logging.info(msg='question_list: category={:,}, total={:,}'.format(len(question_list), count))
        return

    def insert_user_list(self, data_path='', category=''):
        """ 사용자 목록을 elastic-search 에 저장한다.

        :param data_path: 사용자 목록이 저장된 경로
        :param category: 카테고리 정보

        expert 사용자 정보 (랭킹)::

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

        elite 년도별 전문가::

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
                "profilePhotoUrl": "https://kin-phinf.pstatic.net/20180426_110/1524732986074Gv6GP_JPEG/
                    %BA%CE%C7%B0%C1%A4%B8%AE.jpg?type=w200",
                "selectBestCnt": 2997,
                "u": "X/XrUkwNpssPPgqPB+TNUGm+PjMq/YHPNL4nAHhrM74=",
                "viewId": "박학다식전문가",
                "year": 2018
            }

        분야별 지식인 (partner)::

            GyOWWwK059X2dLySrX%2Fd6uWqE60LWxo1q2tZ9d5IOc8%3D	우리세무사
            JikckmNyrpnFIST1cyw44Nbizfuto0Tb0LrSrUSgILw%3D	깊은샘

            {
                "u": "GyOWWwK059X2dLySrX%2Fd6uWqE60LWxo1q2tZ9d5IOc8%3D",
                "viewId": "우리세무사"
            }

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

    @staticmethod
    def get_columns(cursor):
        """"""
        return [d[0] for d in cursor.description]

    def insert_answer_list(self, data_path=''):
        """ 답변 목록을 elastic-search 에 입력한다.

        :param data_path: 사용자 목록이 저장된 경로 data/naver/kin/by_user.economy
            답변 자료 구조::

                {
                    "kinupPoint": 1,
                    "isBest": false,
                    "isContainsLocation": false,
                    "isOne2OneAnswer": false,
                    "isSelectBest": false,
                    "showAdultMark": false,
                    "title": "화물운송관련해서 궁금하게 있어서 올립니다.",
                    "style": "NORMAL",
                    "kinupCnt": 1,
                    "articleOpenYn": "Y",
                    "gdId": "10000009_00000fc80f93",
                    "detailUrl": "/mobile/qna/detail.nhn?d1Id=4&dirId=40607&docId=264769427",
                    "isIng": false,
                    "inputDevice": "PC",
                    "answerNo": 1,
                    "dirId": 40607,
                    "isContainsAudio": false,
                    "isContainsMovie": false,
                    "previewContents": "안녕하세요? 한국무역의 도움이 네이버 지식파트너 한국무역협회입니다. 영업용 개별화물 운송관련 카페에 가입하시어 정보공유 및 질의 해 보세요. 지...",
                    "isContainsImage": false,
                    "docId": 264769427,
                    "formattedWriteTime": "2016.11.30.",
                    "isNetizenBest": false,
                    "openFlag": true
                }
        :return:
        """
        import json
        import shutil

        from os import listdir
        from os.path import isdir, join

        table_name = 'answer_list'

        # 인덱스명 설정
        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = table_name

        from_sqlite = False
        bulk_size = 1000

        # 파일 로딩
        for file in listdir(data_path):
            filename = join(data_path, file)
            if isdir(filename):
                continue

            logging.info(msg='filename: {}'.format(filename))

            if from_sqlite is True:
                # sqlite all data fetch
                conn, cursor = self.open_sqlite(filename=filename, table_name=table_name)

                sql = 'SELECT * FROM {}'.format(table_name)
                cursor.execute(sql)

                for row in cursor.fetchall():
                    doc = json.loads(row[3])

                    doc['_id'] = '{}-{}-{}'.format(row[0], row[1], row[2])

                    self.save_elastic(document=doc, elastic_info=self.elastic_info,
                                      db_name=table_name, insert=True, bulk_size=bulk_size)

                conn.close()

                # 완료 파일 이동
                shutil.move(filename, '{}/done/{}'.format(data_path, file))
            else:
                # 질문 로딩
                token = data_path.strip('/').split('/')

                section = token[-2].replace('by_user.', '').replace('.done', '')
                user_name = token[-1]

                with open(filename, 'r') as fp:
                    body = '\n'.join(fp.readlines())

                    doc_list = json.loads(body)

                    # 카테고리별로 분리
                    for doc in doc_list:
                        dir_id = doc['dirId']

                        doc['_id'] = '{}-{}-{}'.format(str(dir_id)[0], str(dir_id), doc['docId'])

                        if 'section' not in doc:
                            doc['section'] = section

                        if 'user_name' not in doc:
                            doc['user_name'] = user_name

                        self.save_elastic(document=doc, elastic_info=self.elastic_info,
                                          db_name=table_name, insert=True, bulk_size=bulk_size)

        self.save_elastic(document=None, elastic_info=self.elastic_info,
                          db_name=table_name, insert=True, bulk_size=0)

        return

    def merge_question(self, data_path='detail.json.bz2', result_filename='detail.xlsx'):
        """ 네이버 지식인 질문 목록 결과를 취합한다.

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

    def parse_content(self, html, soup=None):
        """ 상세 정보 HTML 을 파싱한다.

        :param html: html
        :param soup: soup
        :return: 파싱된 결과
        """
        import re
        from bs4 import BeautifulSoup

        if html is not None:
            soup = BeautifulSoup(html, 'html5lib')

        if soup is None:
            return None, None

        # 테그 정리
        self.replace_tag(soup, ['script', 'javascript', 'style'])

        self.remove_comment(soup)
        self.remove_banner(soup=soup)
        self.remove_attribute(soup, ['onclick', 'role', 'style', 'data-log'])

        result = {}
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

            result[item['key']] = value_list

        return result, soup

    def trace_tag(self, soup, tag_list, index, result):
        """ 전체 HTML 문서에서 원하는 값을 가진 태그를 찾는다.

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

        soup = soup.findAll(tag_list[index]['name'], attrs=tag_list[index]['attribute'])

        if isinstance(soup, element.ResultSet):
            for tag in soup:
                self.trace_tag(soup=tag, tag_list=tag_list, index=index + 1, result=result)

        return

    @staticmethod
    def remove_comment(soup):
        """ html 태그 중에서 주석 태그를 제거한다.

        :param soup: 웹페이지 본문
        :return: True/False
        """
        from bs4 import Comment

        for element in soup(text=lambda text: isinstance(text, Comment)):
            element.extract()

        return True

    @staticmethod
    def remove_banner(soup):
        """ 자살 방지 베너 삭제를 삭제한다.

        :param soup:
        :return:
        """
        tag_list = soup.findAll('div', {'id': 'suicidalPreventionBanner'})
        for tag in tag_list:
            tag.extract()

        return soup

    @staticmethod
    def remove_attribute(soup, attribute_list):
        """ 속성을 삭제한다.

        :param soup: html 객체
        :param attribute_list: onclick
        :return:
        """

        for tag in soup.findAll(True):
            if len(tag.attrs) == 0:
                continue

            new_attribute = {}
            for name in tag.attrs:
                if name in attribute_list:
                    continue

                if 'javascript' in tag.attrs[name] or 'void' in tag.attrs[name] or '#' in tag.attrs[name]:
                    continue

                new_attribute[name] = tag.attrs[name]

            tag.attrs = new_attribute

        return soup

    def insert_detail(self, filename):
        """질문 상세 페이지를 elastic-search 에 입력한다.

        :param filename: sqlite 파일명
        :return:
        """
        table_name = 'detail'

        # 인덱스명 설정
        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = table_name

        conn, cursor = self.open_sqlite(filename=filename, table_name=table_name)

        sql = 'SELECT d1_id, dir_id, doc_id, content ' \
              'FROM {}'.format(table_name)
        cursor.execute(sql)

        bulk_size = 200

        for row in cursor:
            doc, soup = self.parse_content(row[3])

            content = str(soup.prettify())

            doc['_id'] = '{}-{}-{}'.format(row[0], row[1], row[2])
            doc['html'] = content

            self.save_elastic(document=doc, elastic_info=self.elastic_info,
                              db_name=table_name, insert=True, bulk_size=bulk_size)

        self.save_elastic(document=None, elastic_info=self.elastic_info,
                          db_name=table_name, insert=True, bulk_size=0)

        cursor.close()

        conn.close()

        return


class Crawler(NaverKinUtils):
    """ 네이버 지식인 크롤러 """

    def __init__(self):
        """ 생성자 """
        super().__init__()

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

    def batch_question_list(self):
        """ 질문 목록 전부를 가져온다.

        :return: 없음
        """
        url = 'https://m.kin.naver.com/mobile/qna/kinupList.nhn?' \
              'sortType=writeTime&resultMode=json&dirId={dir_id}&countPerPage={size}&page={page}'

        dir_id_list = [4, 11, 1, 2, 3, 8, 7, 6, 9, 10, 5, 13, 12, 20]
        for dir_id in dir_id_list:
            self.get_question_list(url=url, dir_id=dir_id, end=500)

        return

    def get_question_list(self, url, dir_id=4, start=1, end=90000, size=20):
        """ 네이버 지식인 경제 분야 질문 목록을 크롤링한다.

        :param url:
            쿼리 조회 URL 패턴::

                https://m.kin.naver.com/mobile/qna/kinupList.nhn?
                    sortType=writeTime
                    &resultMode=json
                    &dirId={dir_id}
                    &countPerPage={size}
                    &page={page}

        :param dir_id: 도메인 (4: 경제)
        :param start: 시작 페이지
        :param end: 종료 페이지
        :param size: 페이지 크기
        :return: 없음
        """
        import requests
        from time import sleep

        delay = 5
        bulk_size = 100

        table_name = 'question_list'

        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = table_name

        for page in range(start, end):
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

            logging.info(msg='{} {:,} ~ {:,} {:,}'.format(dir_id, page, end, len(result_list)))

            # 결과 저장
            for doc in result_list:
                doc['_id'] = '{}-{}-{}'.format(doc['d1Id'], doc['dirId'], doc['docId'])

                self.save_elastic(document=doc, elastic_info=self.elastic_info,
                                  db_name=table_name, insert=True, bulk_size=bulk_size)

            self.save_elastic(document=None, elastic_info=self.elastic_info,
                              db_name=table_name, insert=True, bulk_size=0)

            sleep(delay)

        return

    def get_detail(self, index='question_list', match_phrase=None):
        """질문/답변 상세 페이지를 크롤링한다.

        :param index: 인덱스명 question_list, answer_list
        :param match_phrase: "fullDirNamePath": "주식"
        :return:
            https://m.kin.naver.com/mobile/qna/detail.nhn?d1id=4&dirId=40308&docId=303328933
            https://m.kin.naver.com/mobile/qna/detail.nhn?d1Id=6&dirId=60222&docId=301601614
        """
        import json
        import requests
        from time import sleep

        from bs4 import BeautifulSoup

        delay = 5

        url_frame = 'https://m.kin.naver.com/mobile/qna/detail.nhn?dirId={dirId}&docId={docId}'

        query = {
            '_source': 'd1Id,dirId,docId'.split(','),
            'size': '1000',
            'query': {
                'bool': {
                    'must': {
                        'match_phrase': {
                            'fullDirNamePath': '주식'
                        }
                    }
                }
            }
        }

        if match_phrase is not None:
            if isinstance(match_phrase, str):
                match_phrase = json.loads(match_phrase)

            query['query']['bool']['must']['match_phrase'] = match_phrase

        question_list, elastic = self.get_document_list(index=index, query=query)

        detail_index = 'detail'

        # 저장 인덱스명 설정
        self.elastic_info['index'] = detail_index
        self.elastic_info['type'] = detail_index

        i = -1
        size = len(question_list)

        for question in question_list:
            if 'd1Id' not in question:
                question['d1Id'] = str(question['dirId'])[0]

            i += 1
            doc_id = '{}-{}-{}'.format(question['d1Id'], question['dirId'], question['docId'])

            exists = elastic.exists(index=detail_index, doc_type=detail_index, id=doc_id)
            if exists is True:
                logging.info(msg='skip {} {}'.format(doc_id, detail_index))
                continue

            request_url = url_frame.format(**question)

            # 질문 상세 페이지 크롤링
            logging.info(msg='상세 질문: {:,}/{:,} {} {}'.format(i, size, doc_id, request_url))
            request_result = requests.get(url=request_url, headers=self.headers,
                                          allow_redirects=True, timeout=60)

            # 저장
            soup = BeautifulSoup(request_result.content, 'html5lib')

            content = soup.find('div', {'class': 'sec_col1'})
            if content is None:
                continue

            detail_doc, content = self.parse_content(html=None, soup=content)

            detail_doc['_id'] = doc_id
            detail_doc['html'] = str(content.prettify())

            self.save_elastic(document=detail_doc, elastic_info=self.elastic_info,
                              db_name=detail_index, insert=True, bulk_size=0)

            sleep(delay)

        return

    @staticmethod
    def batch_answer_list(user_filename='society.user-list'):
        """사용자별 답변 목록를 가져온다.

        :param user_filename: 사용자 목록 파일명
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
            # target_path = '{data_path}/{user_name}'.format(data_path=result_path, user_name=user_name)

            # self.get_question_list(url=query_url, dir_id=0)

        return

    def get_partner_list(self):
        """지식 파트너 목록을 크롤링한다.

        저장 구조::

            {
              "countPerPage": 10,
              "page": 1,
              "totalCount": 349,
              "isSuccess": true,
              "queryTime": "2018-07-13 16:28:46",
              "lists": [
                {
                  "partnerName": "여성가족부.한국청소년상담복지개발원",
                  "bestAnswerRate": 70.5,
                  "bestAnswerCnt": 10083,
                  "u": "6oCfeacJKVQGwsBB7OHEIS4miiPixwQ%2FoueervNeYrg%3D",
                  "userActiveDirs": [
                    {
                      "divisionIds": [],
                      "masterId": 0,
                      "dirType": "NONLEAF",
                      "localId": 0,
                      "sexFlag": "N",
                      "parentId": 20,
                      "dbName": "db_worry",
                      "open100Flag": "N",
                      "topShow": "N",
                      "relatedIds": "0",
                      "restFlag": "N",
                      "namePath": "고민Q&A>아동, 미성년 상담",
                      "hiddenFlag": "N",
                      "adultFlag": "N",
                      "linkedId": "0",
                      "displayFlag": 0,
                      "dirName": "아동, 미성년 상담",
                      "templateIds": [],
                      "depth": 2,
                      "dirId": 2001,
                      "linkId": 0,
                      "didPath": "20>2001",
                      "childCnt": 7,
                      "edirId": 0,
                      "expertListType": "",
                      "popular": "N",
                      "showOrder": 0
                    }
                  ],
                  "memberViewType": false,
                  "viewType": "ANSWER",
                  "photoUrl": "https://kin-phinf.pstatic.net/20120727_216/1343367618928V5OzE_JPEG/%B3%D7%C0%CC%B9%F6%BF%EB%B7%CE%B0%ED%28300.3000%29.jpg"
                },
                (...)
              ]
            }
        :return:
        """
        import requests
        from time import sleep

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        url_frame = 'https://m.kin.naver.com/mobile/people/partnerList.nhn' \
                    '?resultMode=json&m=partnerList&page={page}&dirId=0'

        table_name = 'partner_list'

        # 인덱스명 설정
        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = table_name

        for page in range(1, 1000):
            request_url = url_frame.format(page=page)

            request_result = requests.get(url=request_url, headers=headers,
                                          allow_redirects=True, timeout=30, verify=False)

            result = request_result.json()

            if 'lists' in result:
                size = len(result['lists'])
                if size == 0:
                    break

                logging.info(msg='{}, {}'.format(size, request_url))

                for doc in result['lists']:
                    doc['_id'] = doc['u']

                    self.save_elastic(document=doc, elastic_info=self.elastic_info,
                                      db_name=table_name, insert=True, bulk_size=100)

            self.save_elastic(document=None, elastic_info=self.elastic_info,
                              db_name=table_name, insert=True, bulk_size=0)
            sleep(5)

        return

    def get_expert_list(self):
        """분야별 전문가 목록을 크롤링한다.

            반환 구조::

                {
                  "result": [
                    {
                      "locationUrl": "http://map.naver.com/local/siteview.nhn?code=71373752",
                      "occupation": "전문의",
                      "companyOpen": "Y",
                      "organizationName": "하이닥",
                      "expertRole": 1,
                      "encodedU": "%2F3soE1QYD7D3mkrmubU2VOr7v7y2zOUWTkk2cj31yRU%3D",
                      "organizationId": 2,
                      "companyName": "고운마취통증의학과의원",
                      "photo": "https://kin-phinf.pstatic.net/exphoto/expert/65/fourlong_1452051150989.jpg",
                      "homepage": "http://gwpainfree.com",
                      "country": "",
                      "area": "경남",
                      "locationOpen": "Y",
                      "answerCount": 5587,
                      "writeTime": "2016-01-06 12:15:59.0",
                      "edirId": 3,
                      "divisionId": 1,
                      "companyPosition": "원장",
                      "workingArea": "domestic",
                      "name": "노민현",
                      "homepageOpen": "Y",
                      "edirName": "마취통증의학과"
                    },
                    (...)
                  ],
                  "totalCount": 10,
                  "errorMsg": "",
                  "isSuccess": true
                }
        """
        import requests
        from time import sleep
        from urllib.parse import unquote

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        expert_type_list = ['doctor', 'lawyer', 'labor', 'animaldoctor', 'pharmacist', 'taxacc', 'dietitian']

        url_frame = 'https://m.kin.naver.com/mobile/ajax/getExpertListAjax.nhn' \
                    '?resultMode=json&m=getExpertListAjax&expertType={expert_type}&page={page}&all=0'

        table_name = 'expert_user_list'

        # 인덱스명 설정
        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = table_name

        for expert_type in expert_type_list:
            for page in range(1, 1000):
                request_url = url_frame.format(expert_type=expert_type, page=page)

                request_result = requests.get(url=request_url, headers=headers,
                                              allow_redirects=True, timeout=30, verify=False)

                result = request_result.json()

                if 'result' in result:
                    size = len(result['result'])
                    if size == 0:
                        break

                    logging.info(msg='{}, {}'.format(size, request_url))

                    for doc in result['result']:
                        doc['expert_type'] = expert_type

                        doc['u'] = unquote(doc['encodedU'])
                        doc['_id'] = doc['u']

                        self.save_elastic(document=doc, elastic_info=self.elastic_info,
                                          db_name=table_name, insert=True, bulk_size=100)

                self.save_elastic(document=None, elastic_info=self.elastic_info,
                                  db_name=table_name, insert=True, bulk_size=0)
                sleep(5)

        return

    def get_elite_user_list(self):
        """ 명예의 전당 채택과 년도별 사용자 목록을 가져온다.

        :return:
        """
        import requests
        from time import sleep

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        month = 0
        for year in range(2012, 2019):
            table_name = 'expert_user_list_{}'.format(year)

            # 인덱스명 설정
            self.elastic_info['index'] = table_name
            self.elastic_info['type'] = table_name

            url = 'https://kin.naver.com/hall/eliteUser.nhn?year={}'.format(year)

            result = requests.get(url=url, headers=headers,
                                  allow_redirects=True, timeout=30, verify=False)

            cookies = requests.utils.dict_from_cookiejar(result.cookies)
            logging.info(msg='eliteUser cookie: {} {}'.format(result, cookies))

            headers['referer'] = url

            for page in range(1, 6):
                list_url = 'https://kin.naver.com/ajax/eliteUserAjax.nhn' \
                           '?year={}&month={}&page={}'.format(year, month, page)

                request_result = requests.get(url=list_url, headers=headers, cookies=cookies,
                                              allow_redirects=True, timeout=60)

                result = request_result.json()

                if 'eliteUserList' in result:
                    logging.info(msg='{}, {}'.format(len(result['eliteUserList']), list_url))

                    for doc in result['eliteUserList']:
                        doc['_id'] = doc['u']

                        self.save_elastic(document=doc, elastic_info=self.elastic_info,
                                          db_name=table_name, insert=True, bulk_size=100)

                    self.save_elastic(document=None, elastic_info=self.elastic_info,
                                      db_name=table_name, insert=True, bulk_size=0)
                sleep(5)

        return

    def get_rank_user_list(self):
        """ 분야별 전문가 목록을 추출한다.

        :return:
        """
        import requests
        from time import sleep

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        url_frame = 'https://kin.naver.com/qna/directoryExpertList.nhn?dirId={dir_id}'

        list_url_frame = [
            'https://kin.naver.com/ajax/qnaWeekRankAjax.nhn?requestId=weekRank&dirId={dir_id}&page={page}',
            'https://kin.naver.com/ajax/qnaTotalRankAjax.nhn?requestId=totalRank&dirId={dir_id}&page={page}'
        ]

        table_name = 'rank_user_list'

        # 인덱스명 설정
        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = table_name

        for dir_name in self.category_list:
            dir_id = self.category_list[dir_name]
            url = url_frame.format(dir_id=dir_id)

            result = requests.get(url=url, headers=headers,
                                  allow_redirects=True, timeout=30, verify=False)

            cookies = requests.utils.dict_from_cookiejar(result.cookies)
            logging.info(msg='cookie: {} {}'.format(result, cookies))

            headers['referer'] = url

            for u_frame in list_url_frame:
                for page in range(1, 10):
                    list_url = u_frame.format(dir_id=dir_id, page=page)

                    request_result = requests.get(url=list_url, headers=headers, cookies=cookies,
                                                  allow_redirects=True, timeout=60)

                    result = request_result.json()

                    if 'result' in result:
                        logging.info(msg='{}, {}'.format(len(result['result']), list_url))

                        for doc in result['result']:
                            doc['_id'] = doc['u']
                            doc['rank_type'] = dir_name

                            self.save_elastic(document=doc, elastic_info=self.elastic_info,
                                              db_name=table_name, insert=True, bulk_size=100)

                        self.save_elastic(document=None, elastic_info=self.elastic_info,
                                          db_name=table_name, insert=True, bulk_size=0)

                        if len(result['result']) != 20:
                            break

                    sleep(5)

        return

    def get_curation_list(self):
        """큐레이션 목록을 크롤링한다."""
        import requests
        from time import sleep

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) '
                          'AppleWebKit/604.1.38 (KHTML, like Gecko) '
                          'Version/11.0 Mobile/15A372 Safari/604.1'
        }

        url_frame = 'https://m.kin.naver.com/mobile/best/curationListAjax.nhn' \
                    '?curationTimestamp=1521527891000&isMoreDirection=true&count=10&_=1531468917051'

        table_name = 'curation_list'

        # 인덱스명 설정
        self.elastic_info['index'] = table_name
        self.elastic_info['type'] = table_name

        return

    def get_document_list(self, index, query):
        """elastic-search 에서 문서를 검색해 반환한다.

        :param index: 인덱스명
        :param query: 검색 조건
        :return: 문서 목록
        """
        from elasticsearch import Elasticsearch

        # 한번에 가져올 문서수
        size = 1000

        count = 1
        sum_count = 0
        scroll_id = ''
        total = -1

        # 서버 접속
        try:
            elastic = Elasticsearch(hosts=[self.elastic_info['host']], timeout=30)

            if elastic.indices.exists(index) is False:
                self.create_elastic_index(elastic, index)
        except Exception as e:
            logging.error(msg='elastic-search 접속 에러: {}'.format(e))
            return

        result = []

        while count > 0:
            # 스크롤 아이디가 있다면 scroll 함수 호출
            if scroll_id == '':
                search_result = elastic.search(index=index, doc_type=index, body=query, scroll='2m', size=size)
            else:
                search_result = elastic.scroll(scroll_id=scroll_id, scroll='2m')

            # 검색 결과 추출
            scroll_id = search_result['_scroll_id']

            hits = search_result['hits']

            if total != hits['total']:
                total = hits['total']

            count = len(hits['hits'])

            sum_count += count
            logging.info(msg='{} {:,} {:,} {:,}'.format(index, count, sum_count, total))

            for item in hits['hits']:
                result.append(item['_source'])

            # 종료 조건
            if count < size:
                break

        return result, elastic


def init_arguments():
    """ 옵션 설정

    :return:
    """
    import textwrap
    import argparse

    description = textwrap.dedent('''\
# 질문 목록 크롤링
python3 naver_kin_crawler.py -question_list 

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
data_path="data/naver/kin/question_list"
for d in $(ls -1 ${data_path}) ; do
    echo ${d}

    python3 naver_kin_crawler.py -merge_question \\
        -data_path "${data_path}/${d}" \\
        -filename "data/naver/kin/${d}.xlsx" \\
        | bzip2 - > "data/naver/kin/${d}.json.bz2"
done

# 사용자 목록을 DB에 저장
python3 naver_kin_crawler.py -insert_user_list -data_path data/naver/kin/users/partner/economy -category '경제 지식파트너'
python3 naver_kin_crawler.py -insert_user_list -data_path data/naver/kin/users/partner/society -category '사회 지식파트너'
python3 naver_kin_crawler.py -insert_user_list -data_path data/naver/kin/users/expert -category 경제
python3 naver_kin_crawler.py -insert_user_list -data_path data/naver/kin/users/elite -category 년도별

# 질문 상세 목록 분리
python3 naver_kin_crawler.py -insert_detail -filename data/naver/kin/detail/detail2.00.db

# 질문 목록을 DB에 저장
# python3 naver_kin_crawler.py -insert_question_list -data_path data/naver/kin/question_list
# 
# IFS=$'\\n'
# data_path="data/naver/kin/question_list.old"
# for d in $(ls -1 ${data_path}) ; do
#     echo ${d}
# 
#     python3 naver_kin_crawler.py -insert_question_list \\
#         -data_path "${data_path}/${d}"
# done

# 답변 목록을 DB에 저장
python3 naver_kin_crawler.py -insert_answer_list -data_path "data/naver/kin/by_user.economy/(사)한국무역협회"

IFS=$'\\n'
data_path="data/naver/kin/by_user.economy.done"
for d in $(ls -1 ${data_path}) ; do
    echo ${d}

    python3 naver_kin_crawler.py -insert_answer_list \\
        -data_path "${data_path}/${d}"
done


    ''')

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=description)

    # 크롤링
    parser.add_argument('-question_list', action='store_true', default=False,
                        help='질문 목록 크롤링')
    parser.add_argument('-detail', action='store_true', default=False,
                        help='답변 상세 페이지 크롤링')

    parser.add_argument('-answer_list', action='store_true', default=False,
                        help='답변 목록 크롤링 (전문가 답변, 지식 파트너 답변 등)')

    parser.add_argument('-elite_user_list', action='store_true', default=False,
                        help='전문가 목록 크롤링')
    parser.add_argument('-rank_user_list', action='store_true', default=False,
                        help='랭킹 사용자 목록 크롤링')
    parser.add_argument('-partner_list', action='store_true', default=False,
                        help='지식 파트너 목록 크롤링')
    parser.add_argument('-get_expert_list', action='store_true', default=False,
                        help='전문가 목록 크롤링')

    # 결과 취합
    parser.add_argument('-merge_question', action='store_true', default=False,
                        help='질문 목록을 엑셀로 저장')
    parser.add_argument('-parse_content', action='store_true', default=False,
                        help='질문 상세 페이지에서 정보 추출')
    parser.add_argument('-insert_user_list', action='store_true', default=False,
                        help='사용자 목록을 DB에 저장')
    parser.add_argument('-insert_question_list', action='store_true', default=False,
                        help='질문 목록을 DB에 저장')
    parser.add_argument('-insert_answer_list', action='store_true', default=False,
                        help='답변 목록을 DB에 저장')
    parser.add_argument('-insert_detail', action='store_true', default=False,
                        help='질문 상세 디비를 elastic-search 에 저장한다.')

    # 파라메터
    parser.add_argument('-filename', default='data/naver/test-detail.sqlite3', help='')
    parser.add_argument('-result_path', default='data/naver/kin', help='')
    parser.add_argument('-data_path', default='data/naver/kin', help='')
    parser.add_argument('-category', default='', help='')
    parser.add_argument('-index', default='question_list', help='인덱스명')
    parser.add_argument('-match_phrase', default='{"fullDirNamePath": "주식"}', help='검색 조건')

    return parser.parse_args()


def main():
    """메인"""
    args = init_arguments()

    crawler = Crawler()

    if args.question_list:
        crawler.batch_question_list()

    if args.answer_list:
        crawler.batch_answer_list(user_filename=args.filename)

    if args.detail:
        crawler.get_detail(index=args.index, match_phrase=args.match_phrase)

    # 질문 취합
    if args.merge_question:
        crawler.merge_question(data_path=args.data_path, result_filename=args.filename)

    # 사용자 목록 크롤링
    if args.elite_user_list:
        crawler.get_elite_user_list()

    if args.rank_user_list:
        crawler.get_rank_user_list()

    if args.partner_list:
        crawler.get_partner_list()

    if args.get_expert_list:
        crawler.get_expert_list()

    # 크롤링 데이터를 디비에 입력
    if args.insert_user_list:
        crawler.insert_user_list(data_path=args.data_path, category=args.category)

    if args.insert_question_list:
        crawler.insert_question_list(data_path=args.data_path)

    if args.insert_answer_list:
        crawler.insert_answer_list(data_path=args.data_path)

    if args.insert_detail:
        crawler.insert_detail(filename=args.filename)

    return


if __name__ == '__main__':
    main()
