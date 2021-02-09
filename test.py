#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

from airflow.contrib.example_dags.libs.helper import print_stuff
from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'Airflow',
    'start_date': days_ago(2)
}

with DAG(dag_id='test', default_args=default_args, schedule_interval=None) as dag:
    def test_volume_mount():
        with open('/foo/volume_mount_test.txt', 'w') as foo:
            foo.write('Hello')

        return_code = os.system("cat /foo/volume_mount_test.txt")
        assert return_code == 0


    # You can use annotations on your kubernetes pods!
    start_task = PythonOperator(
        task_id="start_task",
        python_callable=print_stuff,
        executor_config={
            "KubernetesExecutor": {
                "annotations": {"test": "annotation"}
            }
        }
    )

    # You can mount volume or secret to the worker pod
    second_task = PythonOperator(
        task_id="four_task",
        python_callable=test_volume_mount,
        executor_config={
            "KubernetesExecutor": {
                "volumes": [
                    {
                        "name": "example-kubernetes-test-volume",
                        "hostPath": {"path": "/tmp/"},
                    },
                ],
                "volume_mounts": [
                    {
                        "mountPath": "/foo/",
                        "name": "example-kubernetes-test-volume",
                    },
                ]
            }
        }
    )

    # Test that we can add labels to pods
    third_task = PythonOperator(
        task_id="non_root_task",
        python_callable=print_stuff,
        executor_config={
            "KubernetesExecutor": {
                "labels": {
                    "release": "stable"
                }
            }
        }
    )

    other_ns_task = PythonOperator(
        task_id="other_namespace_task",
        python_callable=print_stuff,
        executor_config={
            "KubernetesExecutor": {
                "namespace": "airflow",
                "labels": {
                    "release": "stable"
                }
            }
        }
    )

    start_task >> second_task >> third_task
    start_task >> other_ns_task
