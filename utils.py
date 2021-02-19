#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os import getenv
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
import yaml
from datetime import timedelta


def open_config(filename: str) -> dict:
    path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT', '/opt/airflow/dags')
    sub_path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_VOLUME_SUBPATH', 'repo')

    filename = '{}/{}/{}'.format(path, sub_path, filename)

    with open(filename, 'r') as fp:
        data = yaml.load(stream=fp, Loader=yaml.FullLoader)
        return dict(data)


def build_portal_dags(filename: str):
    config = open_config(filename=filename)

    dag = DAG(**config['dag'], default_args={
        **config['default_args'],
        'start_date': days_ago(n=1),
        'retry_delay': timedelta(minutes=10),
        'execution_timeout': timedelta(hours=1)
    })

    task_group = {}
    for item in config['tasks']:
        name = item['category']
        if name not in task_group:
            task_group[name] = []

        task_group[name].append(KubernetesPodOperator(
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
        ))

    return dag, task_group
