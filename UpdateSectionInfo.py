#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import json
import sqlite3

import dateutil.parser


class UpdateSectionInfo:
    """
    """
    def __init__(self):
        pass

    @staticmethod
    def set_pragam(cursor, readonly=True):
        """
        sqlite의 속도 개선을 위한 설정
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

    def make_section_index(self, file_name):
        """
        경제-증권       215     0000520518      [인사] 국민연금공단 기금운용본부        http://news.naver.com/main/read.nhn?oid=215&aid=0000520518
        경제-증권       009     0003865788      국민연금 기금운용본부 운용전략실장에 이수철     http://news.naver.com/main/read.nhn?oid=009&aid=0003865788
        """
        conn = sqlite3.connect(file_name)

        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS section (oid INTEGER, aid INTEGER, section TEXT)')

        self.set_pragam(cursor, readonly=False)

        count = 0
        keys = ['section', 'oid', 'aid', 'title', 'url']
        for line in sys.stdin:
            line = line.strip()
            if line == '':
                continue

            token = line.split('\t')
            try:
                row = dict(zip(keys, token))
            except Exception:
                continue

            sql = 'INSERT INTO section (oid, aid, section) VALUES (?, ?, ?)'
            try:
                cursor.execute(sql, (row['oid'], row['aid'], row['section']))
            except Exception:
                print('error: ', row, line, file=sys.stderr)

            count +=1
            if count % 50000 == 0:
                conn.commit()
                print('{:,}'.format(count), flush=True)

        print('Total: {:,}'.format(count), flush=True)

        conn.commit()

        cursor.close()
        conn.close()

    def make_section_index_from_db(self, section_name):
        """
        """
        conn = sqlite3.connect('{}.sqlite3'.format(section_name))

        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS section (oid INTEGER, aid INTEGER, section TEXT)')

        self.set_pragam(cursor, readonly=False)

        count = 0

        section_conn, section_db = self.open_db(section_name)

        collection_list = section_db.collection_names()

        for collection in collection_list:
            section_cursor = section_db[collection].find({})[:]

            for row in section_cursor:
                if row['_id'] == 'section_id' or row['_id'] == 'last_id':
                    continue

                sql = 'INSERT INTO section (oid, aid, section) VALUES (?, ?, ?)'

                query = None
                if 'query' in row:
                    query = row['query']
                elif 'url' in row:
                    query = row['url']['query']

                if query is None:
                    print('error query: ', row, file=sys.stderr)
                    continue

                section = ''
                if isinstance(row['section'], str) is True:
                    section = row['section']
                else:
                    if 'L2' in row['section']:
                        section = '{}-{}'.format(row['section']['L1'], row['section']['L2'])
                    else:
                        section = '{}'.format(row['section']['L1'])

                if section == '':
                    print('error section: ', row, file=sys.stderr)
                    continue

                try:
                    cursor.execute(sql, (query['oid'], query['aid'], section))
                except Exception:
                    print('error sql: ', sys.exc_info()[0], row, query, section, file=sys.stderr)

                count +=1
                if count % 50000 == 0:
                    conn.commit()
                    print('{:,}'.format(count), flush=True)

            print('Total: {:,}'.format(count), flush=True)

            section_cursor.close()

        section_conn.close()

        conn.commit()

        cursor.close()
        conn.close()

    @staticmethod
    def get_query(url):
        """
        url 에서 쿼리문을 반환
        """
        from urllib.parse import urlparse, parse_qs

        url_info = urlparse(url)
        result = parse_qs(url_info.query)
        for key in result:
            result[key] = result[key][0]

        return result, '{}://{}{}'.format(url_info.scheme, url_info.netloc, url_info.path)

    @staticmethod
    def open_db(db_name, host='gollum01', port=27017):
        """
        몽고 디비 핸들 오픈
        """
        from pymongo import MongoClient

        connect = MongoClient('mongodb://{}:{}'.format(host, port))
        db = connect[db_name]

        return connect, db

    @staticmethod
    def get_url(url):
        """
        url 문자열을 찾아서 반환
        """

        if isinstance(url, str) is True:
            return url
        elif 'simple' in url:
            return url['simple']
        elif 'full' in url:
            return url['full']

        return ''

    def update_domain(self, filename):
        """
        """
        import os

        if os.path.exists(filename) is False:
            print('ERROR: not file', filename)
            return

        new_id = '{oid}-{aid}'
        simple_query = 'oid={oid}&aid={aid}'

        conn = sqlite3.connect(filename)

        cursor = conn.cursor()
        self.set_pragam(cursor, readonly=True)

        for line in sys.stdin:
            line = line.strip()
            if line == '':
                continue

            if line.find("ISODate(") > 0:
                line = re.sub(r'ISODate\("(.+?)"\)', '"\g<1>"', line)

            # json 변환
            document = json.loads(line)

            if '$date' in document['date']:
                document['date'] = document['date']['$date']

            # url 추출
            old_id = document['_id']
            if isinstance(document['url'], str) is True:
                str_url = self.get_url(document['url'])

                query, base_url = self.get_query(str_url)
                str_query = simple_query.format(**query)

                document['_id'] = new_id.format(**query)

                document['url'] = {
                    'full': document['url'],
                    'simple': '{}?{}'.format(base_url, str_query),
                    'query': query
                }

                if 'source_url' in document:
                    document['url']['source'] = document['source_url']
                    del document['source_url']
            else:
                query = document['url']['query']

            # section 정보 추출
            cursor.execute('SELECT section FROM section WHERE oid=? AND aid=?', (int(query['oid']), int(query['aid']),))
            section_list = cursor.fetchall()

            if section_list is None or len(section_list) == 0:
                continue

            if 'section' not in document:
                document['section'] = ''

            section = []
            for row in section_list:
                section.append(row[0])

            section = sorted(section)

            str_section = ','.join(list(set(section)))
            if document['section'] == str_section:
                continue

            document['section'] = str_section

            # 저장 혹은 출력
            print(json.dumps(document, sort_keys=True, ensure_ascii=False), flush=True)

    def change_document_id(self):
        """
        """
        new_id = '{oid}-{aid}'
        simple_query = 'oid={oid}&aid={aid}'

        for line in sys.stdin:
            line = line.strip()
            if line == '':
                continue

            if line.find("ISODate(") > 0:
                line = re.sub(r'ISODate\("(.+?)"\)', '"\g<1>"', line)

            # json 변환
            document = json.loads(line)

            if '$date' in document['date']:
                document['date'] = document['date']['$date']

            # url 추출
            # old_id = document['_id']
            if isinstance(document['url'], str) is True:
                str_url = self.get_url(document['url'])

                query, base_url = self.get_query(str_url)
                str_query = simple_query.format(**query)

                document['_id'] = new_id.format(**query)

                document['url'] = {
                    'full': document['url'],
                    'simple': '{}?{}'.format(base_url, str_query),
                    'query': query
                }

                if 'source_url' in document:
                    document['url']['source'] = document['source_url']
                    del document['source_url']

            # 저장 혹은 출력
            str_document = json.dumps(document, sort_keys=True, ensure_ascii=False)
            str_document = re.sub(r'"date": "(.+?)"', '"date": {"$date": "\g<1>"}', str_document)

            print(str_document, flush=True)

    @staticmethod
    def change_date():
        """
        """
        for line in sys.stdin:
            line = line.strip()
            if line == '':
                continue

            line = re.sub(r'"date": "(.+?)"', '"date": {"$date": "\g<1>"}', line)
            print(line, flush=True)


if __name__ == '__main__':
    """
    """

    update = UpdateSectionInfo()

    # cat 2017-??/*.txt | ../../UpdateSectionInfo.py
    # update.make_section_index('section_economy_2017.sqlite3')

    # update.make_section_index_from_db('naver_section_2016')

    # bzcat naver_economy.2017.json.bz2 | ../../UpdateSectionInfo.py
    # update.update_domain('dictionary/etc/naver_section_2016.sqlite3')

    update.change_document_id()

    # update.change_date()
