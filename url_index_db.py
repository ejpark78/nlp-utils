#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import sqlite3
from time import time


class UrlIndexDB(object):
    """
    크롤링 완료된 URL 목록을 저장하고 비교하는 클래스
    """

    def __init__(self):
        super().__init__()

        self.filename = None

        self.conn = None
        self.cursor = None

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

    def open_db(self, filename=None, delete=False):
        """
        url 을 저장하는 캐쉬 디비(sqlite) 오픈
        :param filename: 파일명
        :param delete: 기존 파일 삭제 여부
        :return:
        """
        if filename is not None:
            self.filename = filename

        if self.filename is None:
            return

        if os.path.exists(self.filename) and delete is True:
            os.remove(self.filename)

        # 디비 연결
        self.conn = sqlite3.connect(self.filename)

        self.cursor = self.conn.cursor()

        # 테이블 생성
        self.cursor.execute('CREATE TABLE IF NOT EXISTS url_list (url TEXT PRIMARY KEY NOT NULL)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS id_list (id TEXT PRIMARY KEY NOT NULL)')

        self.set_pragma(self.cursor, readonly=False)

        # sql 명령 실행
        self.conn.commit()

        return

    @staticmethod
    def get_url(url):
        """
        url 문자열을 찾아서 반환

        :param url:
        :return:
        """

        if isinstance(url, str) is True:
            return url
        elif 'simple' in url and url['simple'] != '':
            return url['simple']
        elif 'full' in url:
            return url['full']

        return url

    def check_url(self, url):
        """
        다운 받을 url 이 디비에 있는지 검사

        :param url: url 주소
        :return: 있으면 True, 없으면 False
        """
        if self.cursor is None:
            return False

        url = self.get_url(url)

        # url 주소 조회
        sql = 'SELECT 1 FROM url_list WHERE url=?'
        self.cursor.execute(sql, (url,))

        row = self.cursor.fetchone()
        if row is not None and len(row) == 1:
            return True

        return False

    def check_id(self, id):
        """
        다운 받을 문서 아이디가 인덱스 디비에 있는지 검사

        :param id: 문서 아이디
        :return: 있으면 True, 없으면 False
        """
        if self.cursor is None:
            return False

        # url 주소 조회
        sql = 'SELECT 1 FROM id_list WHERE id=?'
        self.cursor.execute(sql, (id,))

        row = self.cursor.fetchone()
        if row is not None and len(row) == 1:
            return True

        return False

    def save_url(self, url, id):
        """
        입력 받은 URL 저장

        :param url: url 주소
        :param id: 문서 아이디
        :return:
        """
        if self.cursor is None:
            return

        url = self.get_url(url)

        url_sql = 'INSERT INTO url_list (url) VALUES (?)'
        id_sql = 'INSERT INTO id_list (id) VALUES (?)'
        try:
            self.cursor.execute(url_sql, (url,))
            self.cursor.execute(id_sql, (id,))

            self.conn.commit()
        except sqlite3.IntegrityError as e:
            pass
        except Exception as e:
            logging.error('인덱스 디비 저장 오류', exc_info=e)

        return

    def update_elastic_url_list(self, index, elastic_info, doc_type=None):
        """
        디비에 있는 url 목록을 인덱스 디비에 저장

        :param index: 인덱스명
        :param doc_type: 문서 타입
        :param elastic_info: elastic search 접속 정보
        :return: void
        """
        if self.cursor is None:
            return

        start_time = time()

        if 'host' not in elastic_info or elastic_info['host'] is None:
            logging.warning(msg='서버 접속 정보 없음')
            return

        from elasticsearch import Elasticsearch, helpers

        # 디비 연결
        elastic = Elasticsearch(hosts=[elastic_info['host']], timeout=30)

        query = {
            '_source': ['url'],
            'query': {
                'match_all': {}
            }
        }

        if doc_type is None:
            hits = helpers.scan(client=elastic, scroll='5m', query=query,
                                index=index)
        else:
            hits = helpers.scan(client=elastic, scroll='5m', query=query,
                                index=index, doc_type=doc_type)

        count = 0
        for hit in hits:
            document = hit['_source']

            self.save_url(url=document['url'], id=hit['_id'])

            count += 1
            if count % 20000 == 0:
                self.conn.commit()

        msg = 'url 캐쉬 디비 생성 완료: {:,} {:0.4f} sec'.format(count, time() - start_time)
        logging.info(msg=msg)

        return

    def update_mongodb_url_list(self, db_name, mongodb_info, collection_name=None):
        """
        디비에 있는 url 목록을 인덱스 디비에 저장

        :param db_name: 디비 이름
        :param collection_name: 컬랙션명
        :param mongodb_info: 몽고 디비 접속 정보
        :return: void
        """
        if self.cursor is None:
            return

        start_time = time()

        from utils import Utils as CrawlerUtils

        if collection_name is None:
            if 'collection' in mongodb_info and mongodb_info['collection'] is not None:
                collection_name = mongodb_info['collection']

        if collection_name is None:
            logging.warning(msg='컬랙션 정보 없음')
            return

        # 숫자일 경우 문자로 변경
        if isinstance(collection_name, int) is True:
            collection_name = str(collection_name)

        if 'port' not in mongodb_info:
            mongodb_info['port'] = 27017

        if 'name' in mongodb_info:
            db_name = mongodb_info['db_name']

        # 디비 연결
        connect, mongodb = CrawlerUtils().open_db(host=mongodb_info['host'],
                                                  port=mongodb_info['port'],
                                                  db_name=db_name)

        collection = mongodb.get_collection(collection_name)
        cursor = collection.find({}, {'url': 1, '_id': 1})[:]

        count = 0
        for document in cursor:
            if 'url' in document:
                self.save_url(url=document['url'], id=document['_id'])

            count += 1
            if count % 20000 == 0:
                self.conn.commit()

        cursor.close()
        connect.close()

        self.conn.commit()

        msg = 'url 캐쉬 디비 생성 완료: {:,} {:0.4f} sec'.format(count, time() - start_time)
        logging.info(msg=msg)

        return


if __name__ == '__main__':
    pass
