#!.venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys


def init_arguments():
    """
    옵션 설정

    :return:
    """
    import argparse

    parser = argparse.ArgumentParser(description='batch test')

    parser.add_argument('-train', help='', action='store_true', default=True)

    parser.add_argument('-tagging', help='', action='store_true', default=False)

    parser.add_argument('-test_language_utils', help='', action='store_true', default=False)
    parser.add_argument('-convert_corpus', help='', action='store_true', default=False)
    parser.add_argument('-convert_format', help='', action='store_true', default=False)

    return parser.parse_args()


def main():
    args = init_arguments()

    if args.test_language_utils:
        from language_utils.language_utils import main
        main()

    if args.train:
        from language_utils.crf.trainer import main
        main()

    if args.tagging:
        from language_utils.crf.named_entity_tagger import main
        main()

        # from language_utils.crf.pos_tagger import main
        # main()

    if args.convert_corpus:
        from language_utils.crf.pos_tagger_utils import PosTaggerUtils

        util = PosTaggerUtils()
        util.morph_to_syllable()

    # 개체명 형식 변환
    if args.convert_format:
        from language_utils.crf.named_entity_utils import NamedEntityUtils
        util = NamedEntityUtils()
        util.convert_format()


if __name__ == "__main__":
    main()
