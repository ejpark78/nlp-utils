#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import sys


class CorpusUtils(object):
    """코퍼스 처리 관련 유틸"""

    def __init__(self):
        """ """

    def jisikman(self):
        """"""
        for line in sys.stdin:
            doc = json.loads(line)

            if 'question_content' not in doc or doc['question_content'] is None:
                continue

            item = {
                'id': doc['_id'],
                'question': doc['question_content'].strip()
            }

            if item['question'].find('[꿀') == 0:
                continue

            date = ''

            buf = []
            if 'detail_answers' in doc:
                for answer in doc['detail_answers']:
                    if 'answer_content' not in answer or answer['answer_content'] is None:
                        continue

                    if answer['answer_content'].find('포인트 환불]') > 0:
                        continue

                    answer_item = {
                        'text': answer['answer_content'].strip()
                    }

                    if 'tag_string' in answer:
                        answer_item['tag_string'] = answer['tag_string']

                    if 'answer_source' in answer:
                        answer_item['answer_source'] = answer['answer_source']

                    if 'date' in answer and answer['date'] != '':
                        date = answer['date']

                    if 'reg_date' in answer and answer['reg_date'] != '':
                        date = answer['reg_date']

                    buf.append(answer_item)

            if date != '':
                item['date'] = date

            item['answer'] = buf

            print(json.dumps(item, ensure_ascii=False), flush=True)

        return

    def batch(self):
        """ """
        self.jisikman()

if __name__ == '__main__':
    CorpusUtils().batch()
