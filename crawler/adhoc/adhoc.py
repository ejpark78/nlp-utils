#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

from scrapy import cmdline

os.environ['XDG_CONFIG_HOME'] = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.environ['XDG_CONFIG_HOME'])


def init_arguments() -> dict:
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('--name', default='marketwatch', type=str, help='스파이더명')

    return vars(parser.parse_args())


if __name__ == '__main__':
    params = init_arguments()

    cmdline.execute(['scrapy', 'crawl', '--loglevel', 'DEBUG', params['name']])
