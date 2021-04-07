#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from glob import glob

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open('version', 'r') as fp:
    version = ''.join([x.strip() for x in fp.readlines()]).strip()

with open('requirements.txt', 'r') as fp:
    install_requires = [x.strip() for x in fp.readlines()]

setup(
    name='corpus',
    version=version,
    packages=find_packages(include=['corpus', 'corpus.*']),
    python_requires='>=3',
    url='http://galadriel02.korea.ncsoft.corp/searchtf/pypi/nlplab',
    license='Apache License Version 2.0',
    author='ejpark',
    author_email='ejpark@ncsoft.com',
    description='nlplab 데이터셋 배포 라이브러리',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=install_requires,
    include_package_data=True,
    scripts=glob('bin/*.sh'),
    zip_safe=False
)
