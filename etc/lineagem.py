#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import json
import dateutil.parser

from xlsxwriter.workbook import Workbook
from pymongo import MongoClient
from bs4 import BeautifulSoup


def parse_argument():
    """
    옵션 설정
    """
    import argparse

    arg_parser = argparse.ArgumentParser(description='')

    arg_parser.add_argument('-to_xlsx', help='', action='store_true', default=False)
    arg_parser.add_argument('-make_index', help='', action='store_true', default=False)
    arg_parser.add_argument('-merge_comment', help='', action='store_true', default=False)

    return arg_parser.parse_args()


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


def open_sqlite(filename, delete=True):
    import os

    if os.path.exists(filename) and delete is True:
        os.remove(filename)

    import sqlite3

    conn = sqlite3.connect(filename)

    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS article (article_id TEXT PRIMARY KEY NOT NULL, contents TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS comment (article_id TEXT PRIMARY KEY NOT NULL, contents TEXT)')

    set_pragam(cursor, readonly=False)

    return conn, cursor


def simplify(col_list, document):
    """
    """
    result = {}

    try:
        for k in col_list:
            if k in document:
                result[k] = document[k]

        if 'writer' in result:
            result['writer'] = result['writer']['gameUser']['gameCharacterName']

        if 'contents' in result and result['contents'] is not None:
            soup = BeautifulSoup(result['contents'], 'lxml')
            result['contents'] = soup.get_text()
    except Exception:
        return None

    return result


def make_index():
    """
    """
    title = ['articleId', 'title', 'contents', 'commentCount', 'postDate', 'replyCount', 'url', 'writer', 'hitCount']
    comment_title = ['contents', 'postDate', 'replyCount', 'writer']

    conn, cursor = open_sqlite('lineagem.sqlite3')

    count = 0
    for line in sys.stdin:
        line = line.strip()

        document = json.loads(line)

        document_id = document['_id']
        if 'article' in document:
            document = document['article']

        if document is None or 'articleId' not in document:
            print(document_id, document, flush=True)
            continue

        article_id = document['articleId']

        # 필수 항목 추출
        if document_id.find('comment') < 0:
            sql = 'INSERT INTO article (article_id, contents) VALUES (?, ?)'

            simple = simplify(title, document)
            if simple is None:
                continue
        else:
            sql = 'INSERT INTO comment (article_id, contents) VALUES (?, ?)'

            if 'commentList' not in document:
                continue

            simple_list = []
            for comment in document['commentList']:
                simple = simplify(comment_title, comment)
                if simple is None:
                    continue

                simple_list.append(simple)

            simple = simple_list
            if len(simple) == 0:
                continue

        try:
            str_simple = json.dumps(simple, ensure_ascii=False, sort_keys=True)
            cursor.execute(sql, (article_id, str_simple))

            conn.commit()
        except Exception:
            pass

        print('\r{:,}'.format(count), flush=True, end='')
        count += 1

    conn.close()

    return


def merge_comment():
    """
    """
    conn, cursor = open_sqlite('lineagem.sqlite3', delete=False)

    row_id = 0

    fp = open('lineagem.json', 'w')

    sql = 'SELECT article_id, contents FROM article'
    cursor.execute(sql)

    cursor_comment = conn.cursor()

    for article_row in cursor.fetchall():
        document = json.loads(article_row[1])

        # 댓글 추출
        sql = 'SELECT article_id, contents FROM comment WHERE article_id=?'
        cursor_comment.execute(sql, (article_row[0],))

        document['commentList'] = []
        for comment_row in cursor_comment.fetchall():
            comment = json.loads(comment_row[1])

            uniq = []
            for replay in comment:
                # 중복 제거
                key = '{}:{}'.format(replay['contents'], replay['writer'])
                if key not in uniq:
                    document['commentList'].append(replay)
                    uniq.append(key)

        str_result = json.dumps(document, ensure_ascii=False, sort_keys=True)
        fp.write(str_result + '\n')
        fp.flush()

        print('{:,}'.format(row_id), document['articleId'], document['title'], flush=True)
        row_id += 1

    fp.close()

    cursor_comment.close()

    cursor.close()
    conn.close()
    return


def to_xlsx():
    """
    """
    title = ['articleId', 'title', 'contents', 'commentCount', 'postDate', 'replyCount', 'writer', 'hitCount']
    reply_title = ['articleId', 'contents', 'postDate', 'writer']

    # xlsx 파일 준비
    workbook = Workbook('lineagem.xlsx', {'constant_memory': True})

    worksheet = workbook.add_worksheet('자유')
    worksheet_reply = workbook.add_worksheet('댓글')

    # 제목 출력
    row_id = 0
    for i, k in enumerate(title):
        worksheet.write(row_id, i, k)

    for i, k in enumerate(reply_title):
        worksheet_reply.write(row_id, i, k)

    row_id += 1

    # 컬럼 폭 설정
    width = [10, 15, 50, 10, 15, 10, 10, 10, ]
    for i, w in enumerate(width):
        worksheet.set_column(i, i, w)

    width = [10, 50, 20, 20, ]
    for i, w in enumerate(width):
        worksheet_reply.set_column(i, i, w)

    reply_row_id = 1

    # 엑셀 생성
    for line in sys.stdin:
        line = line.strip()

        document = json.loads(line)

        # 본문 저장
        col_id = 0
        for col in title:
            if col in document and document[col] is not None and isinstance(document[col], dict) is False:
                worksheet.write(row_id, col_id, document[col])
            else:
                worksheet.write(row_id, col_id, '')

            col_id += 1

        row_id += 1

        print('{:,}'.format(row_id), document['articleId'], document['title'], flush=True)

        # 댓글 저장
        if 'commentList' in document and len(document['commentList']) > 0:
            for reply in document['commentList']:
                reply['articleId'] = document['articleId']

                col_id = 0
                for col in reply_title:
                    if col in reply and reply[col] is not None and isinstance(reply[col], dict) is False:
                        worksheet_reply.write(reply_row_id, col_id, reply[col])
                    else:
                        worksheet_reply.write(reply_row_id, col_id, '')

                    col_id += 1

                reply_row_id += 1

                print('>> {:,}'.format(reply_row_id), reply['contents'], flush=True)


    workbook.close()

    return


if __name__ == '__main__':

    args = parse_argument()

    if args.to_xlsx is True:
        to_xlsx()
    elif args.make_index is True:
        make_index()
    elif args.merge_comment is True:
        merge_comment()
    else:
        merge_comment()
