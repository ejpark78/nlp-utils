#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import sys
import json

from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize

from NCKmat import *
from morphtrie import *


class KmatUtils(object):
    """ """

    def __init__(self):
        """ """
        self.args = None

    def init(self, domain):
        """ """
        self.kmat = NCKmat()
        self.rules = MorphTrie()

        self.kmat.load('../rsc', 'UserDict_{}'.format(domain))

        self.rule_file = '../rsc/{}.rule'.format(domain)
        self.rules.loadRuleFile(self.rule_file)

    @staticmethod
    def clean_text(text):
        """ """
        alias = {
            '&lt;': '<',
            '&gt;': '>',
            '&amp;': '&',
            '&apos;': "'",
            '&quot;': '"',
            '&nbsp;': ' ',
            '‘': "'",
            '’': "'",
            '“': '"',
            '”': '"',
        }

        for k in alias:
            if k not in text:
                continue

            text = text.replace(k, alias[k])

        return text

    def fit(self, doc, column, engine):
        """ """
        doc[column] = self.clean_text(doc[column])

        if engine == 'korean':
            tagged_list = self.kmat.run_utf8(doc[column])
            morp = applyPOS(self.rules, tagged_list)  # post-processing
        else:
            # 참고) https://datascienceschool.net/view-notebook/8895b16a141749a9bb381007d52721c1/
            tagged_list = pos_tag(word_tokenize(doc[column]))
            morp = ' '.join(['/'.join(p) for p in tagged_list])

        doc['{}_morp'.format(column)] = morp
        doc['{}_token'.format(column)] = re.sub(r'/[^/]+?( |$|\+)', ' ', morp)

        return

    def batch(self):
        """ """
        self.args = self.init_arguments()

        self.init(domain=self.args.domain)

        for line in sys.stdin:
            if line.strip() == '':
                continue

            doc = json.loads(line)
            self.fit(doc=doc, column=self.args.column, engine=self.args.engine)

            print(json.dumps(doc, ensure_ascii=False), flush=True)

        return

    @staticmethod
    def init_arguments():
        """ 옵션 설정"""
        import argparse

        parser = argparse.ArgumentParser(description='')

        parser.add_argument('--engine', default='korean')
        parser.add_argument('--column', default='korean')
        parser.add_argument('--domain', default='common',
                            choices=['common', 'lineageM', 'economy', 'baseball'])

        return parser.parse_args()


def main():
    """"""
    KmatUtils().batch()
    return


if __name__ == '__main__':
    main()
