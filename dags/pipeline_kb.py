#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator

from crawler_dag_builder import CrawlerDagBuilder


def create_dag(filename):
    _dag, task_group = CrawlerDagBuilder().build_pipeline(filename=filename)

    group_list = []
    for name in task_group:
        grp = DummyOperator(task_id=name, dag=_dag)

        for task in task_group[name]:
            grp.set_downstream(task_or_task_list=task)

        group_list.append(grp)

    return _dag


dag = create_dag(filename='pipeline/kb.yaml')
globals()[dag.dag_id] = dag
