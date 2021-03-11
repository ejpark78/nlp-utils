#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator

from crawler_dag_builder import CrawlerDagBuilder

filename_list = list()
filename_list.append('config/news/ajunews_job.yaml')
for filename in filename_list:
    dag, task_group = CrawlerDagBuilder().build(filename=filename)

    start = DummyOperator(task_id='start', dag=dag)
    group_list = []
    for name in task_group:
        prev = start
        for task in task_group[name]:
            prev.set_downstream(task_or_task_list=task)
            prev = task

    group_list.append(start)

