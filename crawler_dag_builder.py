#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import timedelta
import os
from os import getenv

import yaml
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.utils.dates import days_ago


class CrawlerDagBuilder(object):

    @staticmethod
    def open_config(filename: str) -> dict:
        path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT', '/opt/airflow/dags')
        sub_path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_VOLUME_SUBPATH', 'repo')

        template_filename = os.sep.join([path, sub_path, "config", "template.yaml"])
        template = {}
        if os.path.isfile(template_filename):
            with open(filename, 'r') as fp:
                template = yaml.load(stream=fp, Loader=yaml.FullLoader)
                template = dict(template)

        filename = '{}/{}/{}'.format(path, sub_path, filename)
        filename = os.join([path, sub_path, filename])

        with open(filename, 'r') as fp:
            data = yaml.load(stream=fp, Loader=yaml.FullLoader)
            template.update(dict(data))
            return template

    def build(self, filename: str) -> (DAG, dict):
        config = self.open_config(filename=filename)

        dag = DAG(
            **config['dag'],
            default_args={
                **config['default_args'],
                'start_date': days_ago(n=1),
                'retry_delay': timedelta(minutes=10),
                'execution_timeout': timedelta(hours=1),
            }
        )

        task_group = {}
        for item in config['tasks']:
            name = item['category']
            if name not in task_group:
                task_group[name] = []

            if 'args' in item:
                extra_args = item['args']
            else:
                extra_args = [
                    '--config',
                    item['config'],
                    '--sub-category',
                    item['name'],
                ]

            task_group[name].append(KubernetesPodOperator(
                dag=dag,
                name='task',
                task_id=item['task_id'],
                arguments=config['operator']['args'] + extra_args,
                **config['operator']['params']
            ))

        return dag, task_group

    def build2(self, filename: str) -> (DAG, dict):
        config = self.open_config(filename=filename)

        dag = DAG(
            **config['dag'],
            default_args={
                **config['default_args'],
                'start_date': days_ago(n=1),
                'retry_delay': timedelta(minutes=10),
                'execution_timeout': timedelta(hours=1),
            }
        )

        task_group = {}
        for item in config['tasks']:
            name = item['category']
            if name not in task_group:
                task_group[name] = []

            if 'args' in item:
                extra_args = item['args']
            else:
                extra_args = [
                    '--config',
                    item['config'],
                    '--sub-category',
                    item['name'],
                ]

            task_group[name].append(KubernetesPodOperator(
                dag=dag,
                name='task',
                task_id=item['task_id'],
                arguments=config['operator']['args'] + extra_args,
                **config['operator']['params']
            ))

        return config['dag']['dag_id'], dag, task_group
