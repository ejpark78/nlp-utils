#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .corpus_utils import TedCorpusUtils
from .language import TedLanguage
from .talk_list import TedTalkList
from .talks import TedTalks


class TedCrawler(object):

    def __init__(self):
        super().__init__()

        self.params = self.init_arguments()

    def batch(self):
        if self.params.list is True:
            TedTalkList(params=self.params).batch()

        if self.params.update_talk_list is True:
            TedTalkList(params=self.params).update_talk_list()

        if self.params.talks is True:
            TedTalks(params=self.params).batch()

        if self.params.language is True:
            TedLanguage(params=self.params).batch()

        if self.params.insert_talks is True:
            TedCorpusUtils().batch()

        return

    @staticmethod
    def init_arguments():
        import argparse

        parser = argparse.ArgumentParser()

        parser.add_argument('--list', action='store_true', default=False)
        parser.add_argument('--talks', action='store_true', default=False)
        parser.add_argument('--language', action='store_true', default=False)

        parser.add_argument('--insert_talks', action='store_true', default=False)
        parser.add_argument('--update_talk_list', action='store_true', default=False)

        parser.add_argument('--sleep', default=15, type=int)

        return parser.parse_args()


if __name__ == '__main__':
    TedCrawler().batch()

# find data/ted -size -2k -empty
# find data/ted -size -2k -empty -delete
