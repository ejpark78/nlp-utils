#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os

from airflow import DAG
from airflow.example_dags.libs.helper import print_stuff
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'airflow',
}

log = logging.getLogger(__name__)

try:
    from kubernetes.client import models as k8s

    with DAG(
        dag_id='example_kubernetes_executor_config',
        default_args=default_args,
        schedule_interval=None,
        start_date=days_ago(2),
        tags=['example3'],
    ) as dag:

        # You can use annotations on your kubernetes pods!
        start_task = PythonOperator(
            task_id="start_task",
            python_callable=print_stuff,
            executor_config={
                "pod_override": k8s.V1Pod(metadata=k8s.V1ObjectMeta(annotations={"test": "annotation"}))
            },
        )

        # [START task_with_sidecar]
        sidecar_task = PythonOperator(
            task_id="task_with_sidecar",
            python_callable=print_stuff,
            executor_config={
                "pod_override": k8s.V1Pod(
                    spec=k8s.V1PodSpec(
                        containers=[
                            k8s.V1Container(
                                name="app",
                                image="registry.nlp-utils/crawler:live",
                                args=["ls /config/news/"],
                                command=["bash", "-cx"]
                            ),
                        ]
                    )
                ),
            },
        )
        # [END task_with_sidecar]

        # Test that we can add labels to pods
        third_task = PythonOperator(
            task_id="non_root_task",
            python_callable=print_stuff,
            executor_config={
                "pod_override": k8s.V1Pod(metadata=k8s.V1ObjectMeta(labels={"release": "stable"}))
            },
        )

        other_ns_task = PythonOperator(
            task_id="other_namespace_task",
            python_callable=print_stuff,
            executor_config={
                "KubernetesExecutor": {
                    "namespace": "test-namespace", "labels": {"release": "stable"}
                }
            },
        )

        start_task >> other_ns_task
        start_task >> sidecar_task
except ImportError as e:
    log.warning("Could not import DAGs in example_kubernetes_executor_config.py: %s", str(e))
    log.warning("Install kubernetes dependencies with: pip install apache-airflow['cncf.kubernetes']")
