#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from module.utils.selenium_utils import SeleniumUtils


class FBSplitLang(SeleniumUtils):
    """ ko 에 저장된 영어 그룹을 분리 """

    def __init__(self):
        """ 생성자 """
        super().__init__()

    def batch(self):
        """ """
        self.env = self.init_arguments()

        self.open_db()

        group_list = self.read_config(filename=self.env.config, with_comments=True)

        from_index = 'crawler-facebook-ko'

        for grp in group_list:
            if grp['index'] == from_index:
                continue

            query = {
                'query': {
                    'match_phrase': {
                        'page': grp['page']
                    }
                }
            }

            doc_list = self.elastic.dump(index=from_index, query=query)

            bulk_data = []
            for doc in doc_list:
                if doc['page'] != grp['page']:
                    continue

                doc['_id'] = doc['document_id']
                del doc['document_id']

                doc.update(grp['meta'])

                bulk_data.append({
                    'delete': {
                        '_id': doc['_id'],
                        '_index': from_index,
                    }
                })

                self.elastic.save_document(document=doc, index=grp['index'])

            self.elastic.flush()

            if len(bulk_data) > 0:
                self.elastic.elastic.bulk(
                    index=from_index,
                    body=bulk_data,
                    refresh=True,
                )

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정 """
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--config', default='config/facebook/group.json')

        parser.add_argument('--host', default='https://corpus.ncsoft.com:9200')
        parser.add_argument('--auth', default='crawler:crawler2019')
        parser.add_argument('--index', default='crawler-facebook-ko')
        parser.add_argument('--reply_index', default='crawler-facebook-ko-reply')

        parser.add_argument('--log_path', default='log')

        return parser.parse_args()


if __name__ == '__main__':
    FBSplitLang().batch()
