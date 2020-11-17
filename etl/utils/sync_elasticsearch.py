#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys

import pytz
import urllib3
from dateutil.parser import parse as parse_date
from tqdm.autonotebook import tqdm

from utils.elasticsearch_utils import ElasticSearchUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MESSAGE = 25

logging_opt = {
    'level': MESSAGE,
    'format': '%(message)s',
    'handlers': [logging.StreamHandler(sys.stderr)],
}

logging.addLevelName(MESSAGE, 'MESSAGE')
logging.basicConfig(**logging_opt)

logger = logging.getLogger()


class SyncElasticSearchUtils(object):
    """엘라스틱 서치 동기화 유틸"""

    def __init__(self):
        """ 생성자 """
        self.timezone = pytz.timezone('Asia/Seoul')

    def rename_field(self, doc):
        """필드명을 변경한다."""
        field_info = {
            'photo_list': '',
            'photo_caption': '',
            'replay_list': 'reply_list',
            'replay_count': 'reply_count',
            'replay_html_content': 'reply_html_content',
        }

        for k in field_info:
            if k not in doc:
                continue

            if field_info[k] != '':
                doc[field_info[k]] = doc[k]

            del doc[k]

        # 댓글 날짜에 timezone 정보를 설정한다.
        for k in ['reply_list']:
            if k not in doc or isinstance(doc[k], list) is False:
                continue

            for item in doc[k]:
                if 'date' in item:
                    item['date'] = parse_date(item['date']).astimezone(self.timezone)

        return doc

    @staticmethod
    def get_doc_ids(host, index):
        """ 문서 아이디 목록을 조회한다."""
        elastic = ElasticSearchUtils(
            host=host,
            index=index,
            bulk_size=2000,
        )

        # 문서 목록 덤프
        result = elastic.get_id_list(
            size=10000,
            desc=host.split('@')[-1].split(':')[0],
            index=index,
        )

        return elastic, result

    @staticmethod
    def get_missing_ids(source_ids, target_ids):
        """ 빠진 문서 아이디 목록을 추출한다."""
        result = []
        for doc_id in tqdm(source_ids, dynamic_ncols=True):
            if doc_id in target_ids:
                continue

            result.append(doc_id)

        return result

    @staticmethod
    def get_duplicated_ids(source_ids, target_ids):
        """ 중복된 문서 아이디 목록을 추출한다."""
        result = []
        for doc_id in tqdm(source_ids, dynamic_ncols=True):
            if doc_id not in target_ids:
                continue

            result.append(doc_id)

        return result

    @staticmethod
    def copy_docs(missing_ids, elastic_source, elastic_target, source_index, target_index, source=None):
        """ 빠진 문서를 복사한다."""
        from tqdm import trange

        step = 500
        size = len(missing_ids)

        elastic_target.bulk_size = step

        for i in trange(0, size, step, dynamic_ncols=True):
            st, en = (i, i + step - 1)
            if en > size:
                en = size + 1

            doc_list = []
            elastic_source.get_by_ids(
                id_list=missing_ids[st:en],
                index=source_index,
                source=source,
                result=doc_list,
            )

            for doc in doc_list:
                elastic_target.save_document(
                    index=target_index,
                    delete=False,
                    document=doc,
                )

            elastic_target.flush()

        return

    @staticmethod
    def delete_docs(id_list, elastic, index):
        """ 빠진 문서를 복사한다."""
        from tqdm import trange

        step = 500
        size = len(id_list)

        for i in trange(0, size, step, dynamic_ncols=True):
            st = i
            en = i + step - 1
            if en > size:
                en = size + 1

            elastic.delete_doc_by_id(
                index=index,
                id_list=id_list[st:en],
            )

        return

    def sync_missing_doc(self, source_index, target_index, source_host, target_host):
        """corpus & nlp 의 인덱스를 동기화한다."""
        from pprint import pprint

        print(source_host.split('@')[-1], '->', target_host.split('@')[-1])
        print(source_index, '->', target_index)

        elastic_source, source_ids = self.get_doc_ids(host=source_host, index=source_index)
        elastic_target, target_ids = self.get_doc_ids(host=target_host, index=target_index)

        # 문서 아이디 추출
        missing_ids = {
            'source': self.get_missing_ids(source_ids=target_ids, target_ids=source_ids),
            'target': self.get_missing_ids(source_ids=source_ids, target_ids=target_ids),
        }

        info = {
            'source': {
                'host': source_host,
                'index': source_index,
                'doc size': len(source_ids),
                'missing ids': len(missing_ids['source']),
            },
            'target': {
                'host': target_host,
                'index': target_index,
                'doc size': len(target_ids),
                'missing ids': len(missing_ids['target']),
            }
        }

        print('\n')
        pprint(info)

        del source_ids
        del target_ids

        # 아이디가 없는 문서 덤프
        self.copy_docs(
            missing_ids=missing_ids['target'],
            source_index=source_index,
            target_index=target_index,
            elastic_source=elastic_source,
            elastic_target=elastic_target,
        )

        return

    def update_category(self, source_index, target_index, source_host, target_host):
        """corpus & nlp 의 인덱스를 동기화한다."""
        print(source_host.split('@')[-1], '->', target_host.split('@')[-1])
        print(source_index, '->', target_index)

        elastic_source, source_ids = self.get_doc_ids(host=source_host, index=source_index)

        elastic_target = ElasticSearchUtils(
            host=target_host,
            index=target_index,
            bulk_size=2000,
        )

        source = ['category']

        # 아이디가 없는 문서 덤프
        self.copy_docs(
            source=source,
            missing_ids=list(source_ids.keys()),
            source_index=source_index,
            target_index=target_index,
            elastic_source=elastic_source,
            elastic_target=elastic_target,
        )

        return

    def delete_duplicated_docs(self, source_index, target_index, source_host, target_host):
        """corpus & nlp 의 인덱스를 동기화한다."""
        from pprint import pprint

        if source_host == target_host and source_index == target_index:
            print('error source & target is same!!!')
            return

        print(source_host, '->', target_host)

        elastic_source, source_ids = self.get_doc_ids(host=source_host, index=source_index)
        elastic_target, target_ids = self.get_doc_ids(host=target_host, index=target_index)

        # 문서 아이디 추출
        duplicated_ids = self.get_duplicated_ids(source_ids=source_ids, target_ids=target_ids)

        info = {
            'source': {
                'host': source_host,
                'index': source_index,
                'doc size': len(source_ids),
            },
            'target': {
                'host': target_host,
                'index': target_index,
                'doc size': len(target_ids),
            },
            'duplicated ids': len(duplicated_ids),
        }

        print('\n')
        pprint(info)

        del source_ids
        del target_ids

        # 중복된 문서 삭제
        self.delete_docs(
            index=target_index,
            elastic=elastic_target,
            id_list=duplicated_ids,
        )

        return

    # def sync_docs(self, source_index, target_index, source_host, target_host):
    #     """corpus & nlp 의 인덱스를 동기화한다."""
    #     from tqdm import trange
    #
    #     check_doc_id = False
    #
    #     print(source_host, '->', target_host)
    #
    #     elastic_source, source_ids = self.get_doc_ids(host=source_host, index=source_index)
    #     source_ids = list(source_ids.keys())
    #
    #     elastic_target = ElasticSearchUtils(
    #         host=target_host,
    #         index=target_index,
    #         bulk_size=2000,
    #     )
    #
    #     step = 500
    #     size = len(source_ids)
    #
    #     target_doc_index = {}
    #     for i in trange(0, size, step, dynamic_ncols=True):
    #         st = i
    #         en = i + step
    #         if en > size:
    #             en = size + 1
    #
    #         doc_list = []
    #         elastic_source.get_by_ids(
    #             id_list=source_ids[st:en],
    #             index=source_index,
    #             source=None,
    #             result=doc_list,
    #         )
    #
    #         for doc in doc_list:
    #             if 'date' not in doc:
    #                 continue
    #
    #             doc = self.rename_field(doc=doc)
    #
    #             # index tag 추출
    #             dt = doc['date']
    #             if isinstance(doc['date'], str):
    #                 dt = parse_date(doc['date'])
    #                 if dt.tzinfo is None:
    #                     dt = self.timezone.localize(dt)
    #
    #             new_idx = elastic_target.get_target_index(
    #                 index=target_index,
    #                 split_index=True,
    #                 tag=dt.year,
    #             )
    #
    #             if check_doc_id is True:
    #                 if new_idx not in target_doc_index:
    #                     target_doc_index[new_idx] = elastic_target.get_id_list(
    #                         size=10000,
    #                         desc=new_idx,
    #                         index=new_idx,
    #                     )
    #
    #                 if doc['document_id'] in target_doc_index[new_idx]:
    #                     continue
    #
    #             # 문서 복사
    #             elastic_target.save_document(
    #                 index=new_idx,
    #                 document=doc,
    #             )
    #
    #         elastic_target.flush()
    #
    #     return

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('-sync_missing_doc', action='store_true', default=False, help='인덱스 동기화')
        parser.add_argument('-delete_duplicated_docs', action='store_true', default=False, help='중복 문서 삭제')
        parser.add_argument('-update_category', action='store_true', default=False, help='카테고리 갱신')

        parser.add_argument('-source_index', default=None, help='인덱스명')
        parser.add_argument('-target_index', default=None, help='인덱스명')

        parser.add_argument('-source_host', default='https://corpus.ncsoft.com:9200',
                            help='elastic search 주소')
        parser.add_argument('-target_host', default='https://nlp.ncsoft.com:9200',
                            help='elastic search 주소')

        parser.add_argument('-date_range', default=None, help='날짜 범위')

        parser.add_argument('-split_index', action='store_true', default=False,
                            help='인덱스에 연도 태그 삽입')

        return parser.parse_args()


def main():
    """메인"""
    args = SyncElasticSearchUtils.init_arguments()

    utils = SyncElasticSearchUtils()

    if args.update_category:
        utils.update_category(
            source_host=args.source_host,
            target_host=args.target_host,
            source_index=args.source_index,
            target_index=args.target_index,
        )
        return

    if args.delete_duplicated_docs:
        utils.delete_duplicated_docs(
            source_host=args.source_host,
            target_host=args.target_host,
            source_index=args.source_index,
            target_index=args.target_index,
        )
        return

    # if args.sync_missing_doc and args.split_index:
    #     utils.sync_docs(
    #         source_host=args.source_host,
    #         target_host=args.target_host,
    #         source_index=args.source_index,
    #         target_index=args.target_index,
    #     )
    #     return

    if args.sync_missing_doc:
        utils.sync_missing_doc(
            source_host=args.source_host,
            target_host=args.target_host,
            source_index=args.source_index,
            target_index=args.target_index,
        )

    return


if __name__ == '__main__':
    main()
