#!./venv/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


def convert_corpus():
    from language_utils.crf.pos_tagger_utils import PosTaggerUtils

    util = PosTaggerUtils()

    util.morph_to_syllable()


def train():
    from language_utils.crf.trainer import main
    main()


def tagging():
    from language_utils.crf.pos_tagger import main
    main()


if __name__ == "__main__":
    train()
