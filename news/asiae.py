#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from utils import build_news_dags_with_group

filename = 'config/news/asiae.yaml'
dag, task_group = build_news_dags_with_group(filename=filename)

start = DummyOperator(task_id='start', dag=dag)

group_list = []
for name in task_group:
    grp = DummyOperator(task_id=name, dag=dag)

    prev = start
    for task in task_group[name]:
        grp.set_downstream(task_or_task_list=task)
        prev = task

    group_list.append(grp)
