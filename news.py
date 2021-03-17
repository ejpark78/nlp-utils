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
    dag_id,dag, task_group = CrawlerDagBuilder().build2(filename=filename)

    start = DummyOperator(task_id='start', dag=dag)
    group_list = []
    for name in task_group:
        prev = start
        for task in task_group[name]:
            prev.set_downstream(task_or_task_list=task)
            prev = task
        group_list.append(start)
    return dag_id, dag


filename_list = list()
filename_list.append('config/news/ajunews_job.yaml')
filename_list.append('config/news/ajunews_job_sample.yaml')
filename_list.append('config/news/asiae_job.yaml')
filename_list.append('config/news/ccdailynews_job.yaml')
filename_list.append('config/news/cctoday_job.yaml')
filename_list.append('config/news/chosun-biz_job.yaml')
filename_list.append('config/news/daejon_job.yaml')
filename_list.append('config/news/dailian_job.yaml')
filename_list.append('config/news/donga_job.yaml')
filename_list.append('config/news/dt_job.yaml')
filename_list.append('config/news/edaily_job.yaml')
filename_list.append('config/news/etnews_job.yaml')
filename_list.append('config/news/fnnews_job.yaml')
filename_list.append('config/news/fntimes_job.yaml')
filename_list.append('config/news/gyeonghyang_job.yaml')
filename_list.append('config/news/hani_job.yaml')
filename_list.append('config/news/hankook_job.yaml')
filename_list.append('config/news/honam_job.yaml')
filename_list.append('config/news/idaegu_job.yaml')
filename_list.append('config/news/imaeil_job.yaml')
filename_list.append('config/news/inews24_job.yaml')
filename_list.append('config/news/inews365_job.yaml')
filename_list.append('config/news/iusm_job.yaml')
filename_list.append('config/news/jbdomin_job.yaml')
filename_list.append('config/news/jbnews_job.yaml')
filename_list.append('config/news/jemin_job.yaml')
filename_list.append('config/news/jjan_job.yaml')
filename_list.append('config/news/jnilbo_job.yaml')
filename_list.append('config/news/joins_job.yaml')
filename_list.append('config/news/joongboo_job.yaml')
filename_list.append('config/news/joongdo_job.yaml')
filename_list.append('config/news/kado_job.yaml')
filename_list.append('config/news/kjdaily_job.yaml')
filename_list.append('config/news/knnews_job.yaml')
filename_list.append('config/news/kookje_job.yaml')
filename_list.append('config/news/ksilbo_job.yaml')
filename_list.append('config/news/kwangju_job.yaml')
filename_list.append('config/news/kyeongin_job.yaml')
filename_list.append('config/news/newspeppermint_job.yaml')
filename_list.append('config/news/sbs-biz_job.yaml')
filename_list.append('config/news/wowtv_job.yaml')
filename_list.append('config/news/yeongnam_job.yaml')


for filename in filename_list:
    dag_id, dag = create_dag( filename )
    globals()[dag_id] = dag


