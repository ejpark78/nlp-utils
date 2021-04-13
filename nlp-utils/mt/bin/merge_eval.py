#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import re


class MergeSentenceBleuUtils(object):
    """ """

    def __init__(self):
        """ """

    @staticmethod
    def read_bleu(filename, result):
        """ """
        pattern = '(BLEU|NIST) score using (4|5)-grams = (.+?) for system "0" on segment ([0-9]+) of document'
        pattern = re.compile(pattern)

        with open(filename, 'r') as fp:
            for line in fp.readlines():
                m = re.search(pattern, line)
                if m is None:
                    continue

                score_type = m.group(1)
                score = float(m.group(3))

                doc_id = int(m.group(4)) - 1
                if len(result) <= doc_id:
                    result.append({score_type: score})
                else:
                    result[doc_id][score_type] = score

        return

    @staticmethod
    def read_text(filename, result, tag):
        """ """
        if filename is None:
            return

        with open(filename, 'r') as fp:
            for i, text in enumerate(fp.readlines()):
                result[i][tag] = text.strip()

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('-bleu', default=None, help='')
        parser.add_argument('-src', default=None, help='')
        parser.add_argument('-tgt', default=None, help='')
        parser.add_argument('-tst', default=None, help='')

        return parser.parse_args()

    def batch(self):
        """ """
        args = self.init_arguments()

        result = []

        self.read_bleu(filename=args.bleu, result=result)
        self.read_text(filename=args.src, result=result, tag='src')
        self.read_text(filename=args.tgt, result=result, tag='tgt')
        self.read_text(filename=args.tst, result=result, tag='tst')

        for item in result:
            print(json.dumps(item, ensure_ascii=False), flush=True)

        return


if __name__ == '__main__':
    MergeSentenceBleuUtils().batch()
