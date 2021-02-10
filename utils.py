#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os import getenv

import yaml


def open_config(filename: str) -> dict:
    path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT', '/opt/airflow/dags')
    sub_path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_VOLUME_SUBPATH', 'repo')

    filename = '{}/{}/{}'.format(path, sub_path, filename)

    with open(filename, 'r') as fp:
        data = yaml.load(stream=fp, Loader=yaml.FullLoader)
        return dict(data)
