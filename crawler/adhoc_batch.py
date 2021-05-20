#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import configparser
import os
import sys
from os import getenv, chdir

from scrapy import cmdline

os.environ['XDG_CONFIG_HOME'] = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.environ['XDG_CONFIG_HOME'])


def init_arguments() -> dict:
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('--name', default='marketwatch', type=str, help='스파이더명')
    parser.add_argument('--data-dir', default=getenv('SCRAPY_DATA_DIR', default=None), type=str, help='데이터 경로')

    return vars(parser.parse_args())


def change_data_dir(data_dir: str = None, filename: str = 'scrapy.cfg') -> None:
    if data_dir is None:
        return

    cfg = configparser.ConfigParser()

    cfg.read(filenames=[filename])

    cfg['datadir']['default'] = data_dir

    with open(filename, 'w') as fp:
        cfg.write(fp=fp)

    return None


if __name__ == '__main__':
    params = init_arguments()

    chdir(os.environ['XDG_CONFIG_HOME'])
    change_data_dir(data_dir=params['data_dir'])

    cmdline.execute(['scrapy', 'crawl', '--loglevel', 'INFO', params['name']])
