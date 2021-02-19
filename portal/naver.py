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
from utils import open_config, build_portal_dags

build_portal_dags(filename='config/portal/naver.yaml')


# default_args = {
#     **config['default_args'],
#     'start_date': days_ago(n=1),
#     'retry_delay': timedelta(minutes=10),
#     'execution_timeout': timedelta(hours=1)
# }
#
# with DAG(**config['dag'], default_args=default_args) as dag:
#     start = DummyOperator(task_id='start', dag=dag)
#
#     task_group = {}
#     category_group = {}
#     for item in config['tasks']:
#         name = item['category']
#         if name not in task_group:
#             task_group[name] = []
#
#             category_group[name] = DummyOperator(task_id=name, dag=dag)
#
#         task_group[name].append(KubernetesPodOperator(
#             dag=dag,
#             name='task',
#             task_id=item['task_id'],
#             arguments=config['operator']['args'] + [
#                 '--config',
#                 item['config'],
#                 '--sub-category',
#                 item['name'],
#             ],
#             **config['operator']['params']
#         ))
#
#     start >> category_group.values()
#     for name in task_group:
#         category_group[name] >> task_group[name]
