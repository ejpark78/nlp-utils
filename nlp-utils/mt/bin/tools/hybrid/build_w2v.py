#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import re
import sys
import time
import pickle
import logging
import argparse

# arguments
parser = argparse.ArgumentParser(description='Build Word 2 Vector Model')
# parser.add_argument('-corpus', type=str, help='Corpus file name')
parser.add_argument('-out', type=str, help='Output Word Vector file name')
parser.add_argument('-tag', type=str, help='Part of Speech tag: base, N, V, N_V, ...')

args = parser.parse_args()

from data_utils import DataUtils

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding("utf-8")


if __name__ == '__main__':
    # main
    logging.basicConfig(
        format='%(asctime)s : %(levelname)s : %(message)s',
        level=logging.WARNING)

    util = DataUtils()

    # parse allow tags
    allow_tags = util.parse_allow_tags(tags=args.tag)

    print('allow_tags', allow_tags, file=sys.stderr)

    # read corpus
    data = []
    for line in sys.stdin:
        data.append(line.strip())

    (sentences, poss) = util.tokenize_sentences(
                            sentences=data, allow_tags=allow_tags, ncore=12)

    model, bigram = util.build_word_vector(
                            sentences=sentences, filename_cache=args.out)
