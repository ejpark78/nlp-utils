#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow import DAG

from crawler_dag_builder import CrawlerDagBuilder

def create_dag(filename):
    dag, task_group = CrawlerDagBuilder().build(filename=filename)

    start = DummyOperator(task_id='start', dag=dag)
    group_list = []
    for name in task_group:
        prev = start
        for task in task_group[name]:
            prev.set_downstream(task_or_task_list=task)
            prev = task
        group_list.append(start)
    return dag


filename_list = list()
filename_list.append('news/ajunews_job.yaml')
filename_list.append('news/asiae_job.yaml')
filename_list.append('news/ccdailynews_job.yaml')
filename_list.append('news/cctoday_job.yaml')
filename_list.append('news/chosun-biz_job.yaml')
filename_list.append('news/daejon_job.yaml')
filename_list.append('news/dailian_job.yaml')
filename_list.append('news/donga_job.yaml')
filename_list.append('news/dt_job.yaml')
filename_list.append('news/edaily_job.yaml')
filename_list.append('news/etnews_job.yaml')
filename_list.append('news/fnnews_job.yaml')
filename_list.append('news/fntimes_job.yaml')
filename_list.append('news/gyeonghyang_job.yaml')
filename_list.append('news/hani_job.yaml')
filename_list.append('news/hankook_job.yaml')
filename_list.append('news/honam_job.yaml')
filename_list.append('news/idaegu_job.yaml')
filename_list.append('news/imaeil_job.yaml')
filename_list.append('news/inews24_job.yaml')
filename_list.append('news/inews365_job.yaml')
filename_list.append('news/investing_job.yaml')
filename_list.append('news/iusm_job.yaml')
filename_list.append('news/jbdomin_job.yaml')
filename_list.append('news/jbnews_job.yaml')
filename_list.append('news/jemin_job.yaml')
filename_list.append('news/jjan_job.yaml')
filename_list.append('news/jnilbo_job.yaml')
filename_list.append('news/joins_job.yaml')
filename_list.append('news/joongboo_job.yaml')
filename_list.append('news/joongdo_job.yaml')
filename_list.append('news/kado_job.yaml')
filename_list.append('news/kjdaily_job.yaml')
filename_list.append('news/knnews_job.yaml')
filename_list.append('news/kookje_job.yaml')
filename_list.append('news/ksilbo_job.yaml')
filename_list.append('news/kwangju_job.yaml')
filename_list.append('news/kyeongin_job.yaml')
filename_list.append('news/naeil_job.yaml')
filename_list.append('news/newspeppermint_job.yaml')
filename_list.append('news/sbs-biz_job.yaml')
filename_list.append('news/wowtv_job.yaml')
filename_list.append('news/yeongnam_job.yaml')


for filename in filename_list:
    dag = create_dag(filename)
    globals()[dag.dag_id] = dag


