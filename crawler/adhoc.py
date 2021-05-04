#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from scrapy import cmdline


def init_arguments() -> dict:
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('--name', default='marketwatch', type=str, help='스파이더명')

    return vars(parser.parse_args())


if __name__ == '__main__':
    params = init_arguments()

    cmdline.execute(['scrapy', 'crawl', params['name']])
