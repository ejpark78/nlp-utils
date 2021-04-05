#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator

from crawler_dag_builder import CrawlerDagBuilder

filename = 'config/portal/daum.yaml'
dag, task_group = CrawlerDagBuilder().build(filename=filename)

group_list = []
for name in task_group:
    grp = DummyOperator(task_id=name, dag=dag)
    grp.set_downstream(task_or_task_list=task_group[name])

    group_list.append(grp)

start = DummyOperator(task_id='start', dag=dag)
start.set_downstream(task_or_task_list=group_list)
