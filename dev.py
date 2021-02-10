#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import timedelta
from os import getenv

import yaml
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago


def open_config(filename: str) -> dict:
    path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT', '/opt/airflow/dags')
    sub_path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_VOLUME_SUBPATH', 'repo')

    filename = '{}/{}/{}'.format(path, sub_path, filename)

    with open(filename, 'r') as fp:
        data = yaml.load(stream=fp, Loader=yaml.FullLoader)
        return dict(data)


config = open_config(filename='config/naver.yaml')

default_args = {
    'owner': 'Airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=10),
    'start_date': days_ago(n=0, hour=1),
    'depends_on_past': False,
    'email': ['ejpark@ncsoft.com'],
    'email_on_retry': False,
    'email_on_failure': False,
    'execution_timeout': timedelta(hours=1)
}

with DAG(**config['dag'], default_args=default_args) as dag:
    start = DummyOperator(task_id='start', dag=dag)

    category_list = {}
    for item in config['tasks']:
        name = item['category']

        if name not in category_list:
            category_list[name] = DummyOperator(task_id=name, dag=dag)
            start >> category_list[name]

        task = KubernetesPodOperator(
            dag=dag,
            name='task',
            task_id=item['task_id'],
            arguments=config['operator']['args'] + [
                '--config',
                item['config'],
                '--sub-category',
                item['name'],
            ],
            **config['operator']['params']
        )

        category_list[name] >> task
