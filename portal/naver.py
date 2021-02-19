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

from airflow.operators.dummy_operator import DummyOperator
from utils import open_config

# dag, task_group = build_portal_dags(filename='config/portal/naver.yaml')

filename='config/portal/naver.yaml'
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

start = DummyOperator(task_id='start', dag=dag)

group_list = []
for name in task_group:
    grp = DummyOperator(task_id=name, dag=dag)
    grp >> task_group[name]

    group_list.append(grp)

start >> group_list
