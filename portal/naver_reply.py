#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import timedelta

from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from utils import open_config

config = open_config(filename='config/portal/naver-reply.yaml')

default_args = {
    **config['default_args'],
    'start_date': days_ago(n=1),
    'retry_delay': timedelta(minutes=10),
    'execution_timeout': timedelta(hours=1)
}

with DAG(**config['dag'], default_args=default_args) as dag:
    task_list = []
    for item in config['tasks']:
        task_list.append(KubernetesPodOperator(
            dag=dag,
            name='task',
            task_id=item['task_id'],
            arguments=config['operator']['args'] + item['args'],
            **config['operator']['params']
        ))

    start = DummyOperator(task_id='start', dag=dag)
    start >> task_list
