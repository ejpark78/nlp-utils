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
import yaml


def open_config(filename: str) -> dict:
    with open(filename, 'r') as fp:
        data = yaml.load(stream=fp, Loader=yaml.FullLoader)
        return dict(data)


dag = DAG(
    dag_id='config-test',
    description='naver crawler',
    default_args={
        'owner': 'Airflow',
        'retries': 3,
        'retry_delay': timedelta(minutes=10),
        'start_date': days_ago(n=0, hour=1),
        'depends_on_past': False,
        'email': ['ejpark@ncsoft.com'],
        'email_on_retry': False,
        'email_on_failure': False,
        'execution_timeout': timedelta(hours=1)
    },
    schedule_interval='0,30 * * * *',
    max_active_runs=1
)

env_vars = {
    'ELASTIC_SEARCH_HOST': 'https://corpus.ncsoft.com:9200',
    'ELASTIC_SEARCH_AUTH': 'crawler:crawler2019',
}

params = {
    'namespace': 'airflow',
    'image': 'registry.nlp-utils/crawler:live',
    'image_pull_policy': 'Always',
    'image_pull_secrets': 'registry',
    'is_delete_operator_pod': True,
    'env_vars': env_vars,
    'get_logs': True,
    'cmds': ['python3'],
}

args = [
    '-m',
    'crawler.web_news.web_news',
    '--sleep',
    '10',
]

start = DummyOperator(task_id='start', dag=dag)

category_list = {}
for task_id in 'economy,international,it,living,opinion,politics,society,sports,tv,weather'.split(','):
    category_list[task_id] = DummyOperator(task_id=task_id, dag=dag)

    start >> category_list[task_id]

sub_category = open_config(filename='config/naver.yaml')

for item in sub_category:
    task = KubernetesPodOperator(
        dag=dag,
        name='task',
        task_id=item['task_id'],
        arguments=args + [
            '--config',
            '/config/naver/{}.yaml'.format(item['category']),
            '--sub-category',
            item['name'],
        ],
        **params
    )

    category_list[item['category']] >> task
