#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import bz2
import json
import logging
import pickle
import re
import sys
from io import BufferedReader

from dateutil.parser import parse as parse_date
from tqdm import tqdm

from crawler.utils.logger import LogMessage as LogMsg

MESSAGE = 25

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)

logger = logging.getLogger()


class LineageMChattingUtils(object):
    """리니지M 채팅 로그를 변환한다."""

    def __init__(self):
        """생성자"""

    @staticmethod
    def raw2json(filename, result_filename):
        """리니지M 채팅 로그를 변환한다."""
        msg = {
            'level': 'MESSAGE',
            'message': '리니지M 채팅 로그를 변환',
            'filename': filename,
        }
        logger.log(level=MESSAGE, msg=LogMsg(msg))

        text_index = {}
        with bz2.open(filename, 'rb') as fp:
            bfp = BufferedReader(fp)

            for line in tqdm(bfp.readlines()):
                line = str(line, 'utf-8')

                str_date, text = line.split('\t')

                date_list = [parse_date(d) for d in str_date.split(';') if d.strip() != '']

                text = re.sub(r'[ ]+', ' ', text.strip())

                doc = {
                    'type': 'chatting',
                    'text': text,
                    'source': list(set(date_list)),
                }

                if text not in text_index:
                    text_index[text] = doc
                else:
                    text_index[text]['source'] = list(set(text_index[text]['source'] + doc['source']))

        # pickle 로 저장
        with open(result_filename, 'wb') as fp:
            pickle.dump(text_index, fp)

        return

    @staticmethod
    def merge(filename):
        """개별 파일을 병합한다."""
        from glob import glob

        text_index = {}
        for f in tqdm(glob('{}/*.pkl'.format(filename))):
            with open(f, 'rb') as fp:
                item = pickle.load(fp)

            for text in item:
                doc = item[text]
                if text not in text_index:
                    text_index[text] = doc
                    continue

                if doc['type'] == 'chatting':
                    text_index[text]['source'] += doc['source']

        # 출력
        id_list = {}
        for text in tqdm(text_index):
            item = text_index[text]

            if item['type'] == 'chatting':
                # 제일 작은 아이디를 대표 아이디로 정한다.
                date = sorted(item['source'])[0]
                doc_id = date.strftime('%Y%m%d_%H%M%S')

                item['date'] = date.strftime('%Y-%m-%dT%H:%M:%S+09:00')
                item['count'] = len(item['source'])

                del item['source']
            else:
                doc_id = item['_id']

            # doc id
            if doc_id not in id_list:
                id_list[doc_id] = -1
            id_list[doc_id] += 1

            if item['type'] == 'chatting':
                item['_id'] = 'chatting-{}-{}'.format(doc_id, id_list[doc_id])

            str_line = json.dumps(item, ensure_ascii=False)
            print(str_line)

        return


class LineageMBbsUtils(object):
    """리니지M 게시판 관련 유틸"""

    def __init__(self):
        """생성자"""

    def read_dump_file(self, filename, result, key):
        """Json 파일을 읽는다."""
        msg = {
            'level': 'MESSAGE',
            'message': 'json 파일 로딩',
            'key': key,
            'filename': filename,
        }
        logger.log(level=MESSAGE, msg=LogMsg(msg))

        f_list = [
            'articleId', 'categoryId', 'title', 'contents', 'writerName', 'gameCharacterName',
            'postDate', 'updateDate', 'commentId', 'contentsId', 'contentsType', 'firstReportedDate', 'reason',
            'hitCount', 'goodCount', 'badCount', 'reportCount', 'scrapCount', 'isVisible', 'forceToHide'
        ]

        with bz2.open(filename, 'rb') as fp:
            bfp = BufferedReader(fp)

            count = 0

            buf = ''
            for line in tqdm(bfp.readlines()):
                line = str(line, 'utf-8')

                if line[0] != '\t':
                    continue

                line = line.strip()
                if line == '}' or line == '},':
                    buf += '}'

                    count += 1
                    self.merge_item(buf, f_list, key, result)

                    buf = ''
                    continue

                buf += line

            msg = {
                'level': 'MESSAGE',
                'message': 'item 수량',
                'filename': filename,
                'count': count,
            }
            logger.log(level=MESSAGE, msg=LogMsg(msg))

        return

    @staticmethod
    def merge_item(buf, f_list, key, result):
        """본문, 제목, 댓글을 병합한다."""
        try:
            raw_item = json.loads(buf)
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': 'json loads 에러',
                'buf': buf,
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))
            return

        # slim
        item = {}
        for k in f_list:
            if k in raw_item:
                item[k] = raw_item[k]

        if key not in item:
            return

        article_id = item[key]

        comment_id = None
        if 'commentId' in item:
            if article_id not in result:
                result[article_id] = {}

            comment_id = item['commentId']

        if article_id in result:
            if comment_id is None:
                result[article_id].update(item)
            else:
                if comment_id in result[article_id]:
                    result[article_id][comment_id].update(item)
                else:
                    result[article_id][comment_id] = item
        else:
            if comment_id is None:
                result[article_id] = item
            else:
                result[article_id][comment_id] = item

        return

    def get_text(self, contents):
        """html 형태의 본문을 텍스트로 변환해서 반환한다."""
        import warnings
        from bs4 import BeautifulSoup

        contents = contents.replace('\r', '\n')

        contents = re.sub('</tr>', '</tr>\n', contents, flags=re.IGNORECASE | re.MULTILINE)
        contents = re.sub('</p>', '</p>\n', contents, flags=re.IGNORECASE | re.MULTILINE)
        contents = re.sub('<table', '\n<table', contents, flags=re.IGNORECASE | re.MULTILINE)
        contents = re.sub('</dl>', '</dl>\n', contents, flags=re.IGNORECASE | re.MULTILINE)
        contents = re.sub('<br', '\n<br', contents, flags=re.IGNORECASE | re.MULTILINE)

        warnings.filterwarnings('ignore', category=UserWarning, module='bs4')

        soup = BeautifulSoup(contents, 'lxml')
        text = soup.get_text()

        return self.get_clean_text(text.strip())

    @staticmethod
    def get_clean_text(text):
        """공백을 제거한다."""
        text = text.replace(u'\xa0', u'')

        text = re.sub(r'http[^ ]+', '', text)
        text = re.sub(r'\t+', ' ', text)

        text = re.sub(r'[ ]{4,}', '\n', text)
        text = re.sub(r'\n+', '\n', text)

        text = re.sub('[ ]+', ' ', text)

        return text.strip()

    def get_reported_data(self):
        """신고된 게시물 정보를 추출한다."""
        report = {}
        self.read_dump_file('DealReportedContents.json.bz2', report, 'contentsId')

        alias = {
            1: '게시글',
            2: '댓글'
        }

        for content_id in report:
            item = report[content_id]

            item['contentsType'] = alias[item['contentsType']]
            item['contents'] = item['contents'].replace('<br />', '\n')
            item['contents'] = re.sub('\n+', '\n', item['contents'])

            print(json.dumps(item, ensure_ascii=False, sort_keys=True), flush=True)

        return

    def merge_article(self):
        """게시물과 댓글을 합친다."""
        article = {}
        self.read_dump_file('raw/Article.json.bz2', article, 'articleId')
        self.read_dump_file('raw/ArticleContents.json.bz2', article, 'articleId')
        self.read_dump_file('raw/ReactionArticle.json.bz2', article, 'articleId')

        comment = {}
        self.read_dump_file('raw/Comment.json.bz2', comment, 'articleId')
        self.read_dump_file('raw/ReactionComment.json.bz2', comment, 'articleId')

        for article_id in tqdm(article):
            item = article[article_id]

            if article_id in comment:
                item['comment_list'] = []
                for comment_id in sorted(comment[article_id]):
                    one_comment = comment[article_id][comment_id]
                    if 'contents' in one_comment:
                        one_comment['html_contents'] = one_comment['contents']
                        one_comment['contents'] = self.get_text(one_comment['html_contents'])

                    item['comment_list'].append(one_comment)

            # html 에서 텍스트를 추출한다.
            if 'contents' in item:
                item['html_contents'] = item['contents']
                item['contents'] = self.get_text(item['html_contents'])

            print(json.dumps(item, ensure_ascii=False), flush=True)

        return

    @staticmethod
    def import_data(host, index, filename, mapping):
        """데이터를 elasticsearch에 입력한다."""
        from crawler.utils.es import ElasticSearchUtils

        elastic = ElasticSearchUtils(host=host)

        elastic.bulk_size = 5000

        msg = {
            'level': 'MESSAGE',
            'message': 'import_data 파일 로딩',
            'host': host,
            'index': index,
            'filename': filename,
        }
        logger.log(level=MESSAGE, msg=LogMsg(msg))

        elastic.open()

        elastic.delete_index(conn=elastic.conn, index=index)
        elastic.create_index(conn=elastic.conn, index=index)

        with bz2.open(filename, 'rb') as fp:
            bfp = BufferedReader(fp)

            for line in tqdm(bfp.readlines()):
                line = str(line, 'utf-8')

                doc = json.loads(line)

                elastic.save_document(document=doc, index=index)

            elastic.flush()
        return

    @staticmethod
    def bbs2pkl():
        """전처리된 게시판을 피클로 변환하여 저장한다."""
        tag = '2019-03-21'

        filename = 'data/lineagem/text_pool/{}/bbs.json.bz2'.format(tag)

        bbs_idx = {}
        with bz2.open(filename, 'rb') as fp:
            bfp = BufferedReader(fp)

            for line in tqdm(bfp.readlines()):
                line = str(line, encoding='utf-8')

                doc = json.loads(line)

                bbs_idx[int(doc['articleId'])] = doc

        with open('data/lineagem/text_pool/{}/bbs.pkl'.format(tag), 'wb') as fp:
            pickle.dump(bbs_idx, fp)

        return


class LineageMTextUtils(object):
    """텍스트를 추출한다."""

    def __init__(self):
        """생성자"""

    @staticmethod
    def get_clean_text(text):
        """텍스트 정제"""
        if text.find('●▅▇█▇▆▅▄▇') >= 0:
            return ''

        text = re.sub(r'<img.+?>', '', text)

        text = re.sub(r'\t+', ' ', text)

        if text.find('http') >= 0:
            text = text.replace('<br />', ' ')

            text = re.sub(r'http[^ ]+', '', text)
            text = re.sub(r'<img.+?>', '', text)

            if text.strip() == '':
                return ''

        text = text.replace(u'\xa0', u'')

        text = re.sub(r'[ ]{4,}', '\n', text)
        text = re.sub(r'\n+', '\n', text)

        text = re.sub('[ ]+', ' ', text)

        return text.strip()

    @staticmethod
    def parse_date(item):
        """날짜 파싱"""
        try:
            date = parse_date(item['postDate'])
            str_date = date.strftime('%Y-%m-%dT%H:%M:%S+09:00')
        except Exception as e:
            msg = {
                'level': 'ERROR',
                'message': '날짜 파싱 에러',
                'post_date': item['postDate'],
                'exception': str(e),
            }
            logger.error(msg=LogMsg(msg))
            return None

        return str_date

    def bbs2text(self, filename, result_filename, board_list):
        """bbs에서 text를 추출한다."""
        msg = {
            'level': 'MESSAGE',
            'message': 'bbs에서 텍스트 추출',
            'filename': filename,
        }
        logger.log(level=MESSAGE, msg=LogMsg(msg))

        # 카테고리 필터링
        category_index = None

        board_name = {
            18: 'knowhow',
            3: 'free',
            8: 'event_participate',
            14: 'image',
            20: 'server',
        }

        if board_list is not None:
            category_index = {}

            board_index = {}
            for c_id in board_name:
                board_index[board_name[c_id]] = c_id

            for b_name in board_list.split(','):
                category_index[board_index[b_name]] = b_name

        # 개수
        count = {
            'item': 0,
            'empty_content': 0,
            'empty_comment': 0,
            'date_error': 0,
        }

        text_index = {}

        utils = LineageMBbsUtils()

        with bz2.open(filename, 'rb') as fp:
            bfp = BufferedReader(fp)

            for line in tqdm(bfp.readlines()):
                line = str(line, 'utf-8')

                item = json.loads(line)

                # 카테고리 필터링
                cate_id = item['categoryId']
                if category_index is not None and cate_id not in category_index:
                    continue

                # 문서 아이디 추출
                doc_id = item['articleId']
                str_date = self.parse_date(item)
                if str_date is None:
                    count['date_error'] += 1
                    continue

                count['item'] += 1

                # 제목
                text = self.get_clean_text(item['title'])
                if text != '' and text not in text_index:
                    text_index[text] = {
                        '_id': 'bbs-title-{}'.format(doc_id),
                        'type': 'bbs-title',
                        'date': str_date,
                        'board_name': board_name[cate_id],
                        'text': text,
                    }

                # 본문
                if 'contents' not in item:
                    count['empty_content'] += 1
                else:
                    contents = utils.get_text(item['contents'])

                    text = self.get_clean_text(contents)
                    if text != '' and text not in text_index:
                        text_index[text] = {
                            '_id': 'bbs-contents-{}'.format(doc_id),
                            'type': 'bbs-contents',
                            'date': str_date,
                            'board_name': board_name[cate_id],
                            'text': text,
                        }

                # 댓글
                if 'comment_list' not in item:
                    count['empty_comment'] += 1
                else:
                    for comment in item['comment_list']:
                        if 'contents' not in comment:
                            continue

                        text = self.get_clean_text(comment['contents'])
                        if text == '' or text in text_index:
                            continue

                        str_date = self.parse_date(comment)
                        if str_date is None:
                            count['date_error'] += 1
                            continue

                        text_index[text] = {
                            '_id': 'bbs-comment-{}-{}'.format(doc_id, comment['commentId']),
                            'type': 'bbs-comment',
                            'date': str_date,
                            'board_name': board_name[cate_id],
                            'text': text,
                        }

        # pickle 로 저장
        with open(result_filename, 'wb') as fp:
            pickle.dump(text_index, fp)

        msg = {
            'level': 'MESSAGE',
            'message': '완료',
            'filename': filename,
            'result_filename': result_filename,
            'count': count,
        }
        logger.log(level=MESSAGE, msg=LogMsg(msg))

        return


def init_arguments():
    """ 옵션 설정"""
    import argparse

    parser = argparse.ArgumentParser(description='')

    parser.add_argument('-text_bbs', action='store_true', default=False, help='')
    parser.add_argument('-text_unique', action='store_true', default=False, help='')

    parser.add_argument('-chatting', action='store_true', default=False, help='채팅 로그 변환')

    parser.add_argument('-import_data', action='store_true', default=False, help='')
    parser.add_argument('-merge_article', action='store_true', default=False, help='')
    parser.add_argument('-merge', action='store_true', default=False, help='')

    parser.add_argument('-bbs2text', action='store_true', default=False, help='')

    parser.add_argument('-get_reported_data', action='store_true', default=False, help='')

    parser.add_argument('-filename', default='', help='')
    parser.add_argument('-result_filename', default='', help='')

    parser.add_argument('-host', default='https://corpus:corpus2019@corpus.ncsoft.com:9200', help='')
    parser.add_argument('-mapping', default='', help='')
    parser.add_argument('-index', default='', help='')

    parser.add_argument('-board_list', default=None, help='')

    return parser.parse_args()


def main():
    """메인 함수"""
    args = init_arguments()

    if args.merge_article:
        LineageMBbsUtils().merge_article()

    if args.get_reported_data:
        LineageMBbsUtils().get_reported_data()

    if args.import_data:
        LineageMBbsUtils().import_data(
            host=args.host,
            index=args.index,
            filename=args.filename,
            mapping=args.mapping,
        )

    if args.bbs2text:
        LineageMTextUtils().bbs2text(
            filename=args.filename,
            result_filename=args.result_filename,
            board_list=args.board_list,
        )

    if args.chatting:
        LineageMChattingUtils().raw2json(args.filename, args.result_filename)

    if args.merge:
        LineageMChattingUtils().merge(args.filename)

    return


if __name__ == "__main__":
    main()
