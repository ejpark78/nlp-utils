#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from airflow.operators.dummy_operator import DummyOperator
from utils import build_portal_dags

dag, task_group = build_portal_dags(filename='config/portal/naver.yaml')

start = DummyOperator(task_id='start', dag=dag)

group_list = []
for name in task_group:
    grp = DummyOperator(task_id=name, dag=dag)
    grp >> task_group[name]

    group_list.append(grp)

start >> group_list
