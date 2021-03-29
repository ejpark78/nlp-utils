#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from copy import deepcopy
from datetime import timedelta
import os
from os import getenv

import yaml
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.utils.dates import days_ago

import kubernetes.client.models as k8s

class CrawlerDagBuilder(object):

    @staticmethod
    def update_yaml(yaml_1, yaml_2):
        template = deepcopy(yaml_1)
        new_yaml = deepcopy(yaml_2)
        for k in new_yaml.keys():
            if k in template:
                if type(new_yaml[k]) == dict:
                    if type(template[k]) == dict:
                        template[k] = CrawlerDagBuilder.update_yaml(template[k], new_yaml[k])
                    else:
                        continue
                elif type(new_yaml[k]) == list:
                    if type(template[k]) == list:
                        for conf in new_yaml[k]:
                            if conf in template[k]:
                                continue
                            else:
                                template[k].append(conf)
                    else:
                        continue
                else:
                    template[k] = new_yaml[k]
            else:
                template[k] = new_yaml[k]
        return template

    @staticmethod
    def open_config(filename: str) -> dict:
        path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT', '/opt/airflow/dags')
        sub_path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_VOLUME_SUBPATH', 'repo')

        sep = '/'
        filename = sep.join([path, sub_path, filename]
                            if f'config{sep}' in filename
                            else [path, sub_path, 'config', filename])

        with open(filename, 'r', encoding='utf-8') as fp:
            data = yaml.load(stream=fp, Loader=yaml.FullLoader)
            if "reference" in data:
                temp_filename = data["reference"] if '.yaml' in data["reference"] else "template.yaml"
                template_filename = sep.join([path, sub_path, temp_filename]
                                             if f'config{sep}' in data["reference"]
                                             else [path, sub_path, 'config', temp_filename])

                template = {}
                if os.path.isfile(template_filename):
                    with open(template_filename, 'r', encoding='utf-8') as fp:
                        template = yaml.load(stream=fp, Loader=yaml.FullLoader)
                        template = template if '.yaml' in data["reference"] else template[data["reference"]]
                return CrawlerDagBuilder.update_yaml(template, data)
            else:
                return data

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
            if 'init_containers' in config['operator']:
                init_containers_config = config['operator'].pop('init_containers')
                init_containers = [k8s.V1Container(**init_containers_config)]
                pod_operator = KubernetesPodOperator(
                    dag=dag,
                    name='task',
                    task_id=item['task_id'],
                    arguments=config['operator']['args'] + extra_args,
                    init_containers=init_containers,
                    **config['operator']['params']
                )
            else:
                pod_operator = KubernetesPodOperator(
                    dag=dag,
                    name='task',
                    task_id=item['task_id'],
                    arguments=config['operator']['args'] + extra_args,
                    **config['operator']['params']
                )
            task_group[name].append(pod_operator)

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
