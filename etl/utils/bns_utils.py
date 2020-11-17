#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import sys

from dateutil.parser import parse as parse_date

from utils.elasticsearch_utils import ElasticSearchUtils
from utils.sqlite import SqliteUtils

logging_opt = {
    'level': logging.INFO,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.basicConfig(**logging_opt)


class BbsUtils(object):
    """"""

    def __init__(self):
        """생성자"""

    @staticmethod
    def load_comment(filename):
        """"""
        result = {}

        sqlite = SqliteUtils(filename=filename)
        table = sqlite.table_list()[0]

        columns = sqlite.get_columns(table)

        cursor = sqlite.conn.cursor()
        cursor.execute('SELECT * FROM {}'.format(table))

        count = 0
        for val in cursor.fetchall():
            count += 1
            if count % 200 == 0:
                logging.info(msg='loading: {:,d}'.format(count))

            doc = dict(zip(columns, val))
            if 'postDate' in doc:
                date = parse_date(doc['postDate'])
                doc['postDate'] = date.strftime('%Y-%m-%dT%H:%M:%SZ')

            if 'commentId' in doc:
                doc['_id'] = doc['commentId']

            article_id = doc['articleId']
            if article_id not in result:
                result[article_id] = []

            result[article_id].append(doc)

        cursor.close()

        return result

    def merge_comments(self, host, index, article_fn, comment_fn):
        """"""
        comment = self.load_comment(comment_fn)

        self.push_data(host=host, index=index, filename=article_fn, comment=comment)
        return

    @staticmethod
    def push_data(host, index, filename, comment=None):
        """"""
        elastic = ElasticSearchUtils(host=host, index=index)

        sqlite = SqliteUtils(filename=filename)
        table = sqlite.table_list()[0]

        columns = sqlite.get_columns(table)

        cursor = sqlite.conn.cursor()
        cursor.execute('SELECT * FROM {}'.format(table))

        for val in cursor.fetchall():
            doc = dict(zip(columns, val))
            if 'postDate' in doc:
                date = parse_date(doc['postDate'])
                doc['postDate'] = date.strftime('%Y-%m-%dT%H:%M:%SZ')

            if 'commentId' in doc:
                doc['_id'] = doc['commentId']
            elif 'articleId' in doc:
                article_id = doc['articleId']
                doc['_id'] = article_id

                if comment is not None and article_id in comment:
                    doc['comment_list'] = comment[article_id]

            elastic.save_document(document=doc)

        elastic.flush()

        cursor.close()

        return

    @staticmethod
    def qna_push_data(host, index):
        """"""
        elastic = ElasticSearchUtils(host=host, index=index)

        buf = ''
        for line in sys.stdin:
            if '"question":' in line or '"answer":' in line:
                buf = ''
                continue

            if '	}' not in line:
                buf += line
                continue

            buf += '}'

            doc = json.loads(buf, strict=False)
            buf = ''

            for k_date in ['regdate', 'moddate']:
                if k_date not in doc:
                    continue

                date = parse_date(doc[k_date])
                doc[k_date] = date.strftime('%Y-%m-%dT%H:%M:%SZ')

            if 'no' in doc:
                doc['_id'] = doc['no']

            elastic.save_document(document=doc)

        elastic.flush()
        return

    @staticmethod
    def bns_push_data(host, index):
        """"""
        elastic = ElasticSearchUtils(host=host, index=index)

        buf = ''
        for line in sys.stdin:
            if '"BladeNSoul_BBS_article":' in line:
                buf = ''
                continue

            if '	}' not in line:
                buf += line
                continue

            buf += '}'

            doc = json.loads(buf, strict=False)
            buf = ''

            for k_date in ['postDate']:
                if k_date not in doc:
                    continue

                date = parse_date(doc[k_date])
                doc[k_date] = date.strftime('%Y-%m-%dT%H:%M:%SZ')

            if 'articleId' in doc:
                doc['_id'] = doc['articleId']

            elastic.save_document(document=doc)

        elastic.flush()
        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('-bns', help='', action='store_true', default=False)
        parser.add_argument('-qna', help='', action='store_true', default=False)
        parser.add_argument('-merge_comments', help='', action='store_true', default=False)

        parser.add_argument('-filename', default='data/db/AionBBS.db', help='파일명')

        parser.add_argument('-article', default='data/db/LineageM_BBS_article.db', help='파일명')
        parser.add_argument('-comment', default='data/db/LineageM_BBS_comment.db', help='파일명')

        parser.add_argument('-host', default='http://corpus.ncsoft.com:9200', help='elasticsearch 주소')
        parser.add_argument('-index', default='aion-bbs', help='인덱스명')

        return parser.parse_args()


def main():
    """"""
    utils = BbsUtils()

    args = utils.init_arguments()

    if args.qna:
        utils.qna_push_data(host=args.host, index=args.index)
    elif args.bns:
        utils.bns_push_data(host=args.host, index=args.index)
    elif args.merge_comments:
        utils.merge_comments(host=args.host, index=args.index,
                             article_fn=args.article, comment_fn=args.comment)
    else:
        utils.push_data(host=args.host, index=args.index, filename=args.filename)

    return


if __name__ == "__main__":
    main()
