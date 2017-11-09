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

    parser.add_argument('-test_language_utils', help='', action='store_true', default=False)

    return parser.parse_args()


def convert_corpus():
    from language_utils.crf.pos_tagger_utils import PosTaggerUtils

    util = PosTaggerUtils()

    util.morph_to_syllable()


def train():
    from language_utils.crf.trainer import main
    main()

    # from language_utils.crf.trainer import main
    # main()


def tagging():
    from language_utils.crf.named_entity_tagger import main
    main()

    # from language_utils.crf.pos_tagger import main
    # main()


def convert_format():
    from language_utils.crf.named_entity_utils import NamedEntityUtils
    util = NamedEntityUtils()

    # util.test_convert_format_sentence()
    util.convert_format()


def test_language_utils():
    try:
        from language_utils.language_utils import main
    except ImportError:
        sys.path.append(os.path.dirname(os.path.realpath(__file__)))

        from .language_utils import main

    main()


def main():
    args = init_arguments()

    if args.test_language_utils:
        test_language_utils()

    # convert_format()
    train()
    # tagging()


if __name__ == "__main__":
    main()
