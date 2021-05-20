#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open('version', 'r') as fp:
    version = ''.join([x.strip() for x in fp.readlines()]).strip()

with open('requirements.txt', 'r') as fp:
    install_requires = [x.strip() for x in fp.readlines()]

setup(
    name='crawler',
    version=version,
    packages=find_packages(include=['crawler', 'crawler.*']),
    python_requires='>=3',
    url='http://galadriel02.korea.ncsoft.corp/crawler-dev/crawler',
    license='Apache License Version 2.0',
    author='ejpark',
    author_email='ejpark@ncsoft.com',
    description='검색팀 크롤러',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=install_requires,
    include_package_data=True,
    zip_safe=False
)

# ref: https://stackoverflow.com/questions/24347450/how-do-you-add-additional-files-to-a-wheel
# config 하위에 __init__.py 를 넣어야함.
