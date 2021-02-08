#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""
This is an example dag for using the KubernetesPodOperator.
"""

from kubernetes.client import models as k8s

from airflow import DAG
from airflow.kubernetes.secret import Secret
from airflow.operators.bash import BashOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.utils.dates import days_ago

# [START howto_operator_k8s_cluster_resources]
secret_file = Secret('volume', '/etc/sql_conn', 'airflow-secrets', 'sql_alchemy_conn')
secret_env = Secret('env', 'SQL_CONN', 'airflow-secrets', 'sql_alchemy_conn')
secret_all_keys = Secret('env', None, 'airflow-secrets-2')
volume_mount = k8s.V1VolumeMount(
    name='test-volume', mount_path='/root/mount_file', sub_path=None, read_only=True
)

configmaps = [
    k8s.V1EnvFromSource(config_map_ref=k8s.V1ConfigMapEnvSource(name='test-configmap-1')),
    k8s.V1EnvFromSource(config_map_ref=k8s.V1ConfigMapEnvSource(name='test-configmap-2')),
]

volume = k8s.V1Volume(
    name='test-volume',
    persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name='test-volume'),
)

port = k8s.V1ContainerPort(name='http', container_port=80)

init_container_volume_mounts = [
    k8s.V1VolumeMount(mount_path='/etc/foo', name='test-volume', sub_path=None, read_only=True)
]

init_environments = [k8s.V1EnvVar(name='key1', value='value1'), k8s.V1EnvVar(name='key2', value='value2')]

init_container = k8s.V1Container(
    name="init-container",
    image="ubuntu:16.04",
    env=init_environments,
    volume_mounts=init_container_volume_mounts,
    command=["bash", "-cx"],
    args=["echo 10"],
)

affinity = k8s.V1Affinity(
    node_affinity=k8s.V1NodeAffinity(
        preferred_during_scheduling_ignored_during_execution=[
            k8s.V1PreferredSchedulingTerm(
                weight=1,
                preference=k8s.V1NodeSelectorTerm(
                    match_expressions=[
                        k8s.V1NodeSelectorRequirement(key="disktype", operator="in", values=["ssd"])
                    ]
                ),
            )
        ]
    ),
    pod_affinity=k8s.V1PodAffinity(
        required_during_scheduling_ignored_during_execution=[
            k8s.V1WeightedPodAffinityTerm(
                weight=1,
                pod_affinity_term=k8s.V1PodAffinityTerm(
                    label_selector=k8s.V1LabelSelector(
                        match_expressions=[
                            k8s.V1LabelSelectorRequirement(key="security", operator="In", values="S1")
                        ]
                    ),
                    topology_key="failure-domain.beta.kubernetes.io/zone",
                ),
            )
        ]
    ),
)

tolerations = [k8s.V1Toleration(key="key", operator="Equal", value="value")]

# [END howto_operator_k8s_cluster_resources]


default_args = {
    'owner': 'airflow',
}

with DAG(
    dag_id='example_kubernetes_operator',
    default_args=default_args,
    schedule_interval=None,
    start_date=days_ago(2),
    tags=['example'],
) as dag:
    k = KubernetesPodOperator(
        namespace='default',
        image="ubuntu:16.04",
        cmds=["bash", "-cx"],
        arguments=["echo", "10"],
        labels={"foo": "bar"},
        secrets=[secret_file, secret_env, secret_all_keys],
        ports=[port],
        volumes=[volume],
        volume_mounts=[volume_mount],
        env_from=configmaps,
        name="airflow-test-pod",
        task_id="task",
        affinity=affinity,
        is_delete_operator_pod=True,
        hostnetwork=False,
        tolerations=tolerations,
        init_containers=[init_container],
        priority_class_name="medium",
    )

    # [START howto_operator_k8s_private_image]
    quay_k8s = KubernetesPodOperator(
        namespace='default',
        image='quay.io/apache/bash',
        image_pull_secrets=[k8s.V1LocalObjectReference('testquay')],
        cmds=["bash", "-cx"],
        arguments=["echo", "10", "echo pwd"],
        labels={"foo": "bar"},
        name="airflow-private-image-pod",
        is_delete_operator_pod=True,
        in_cluster=True,
        task_id="task-two",
        get_logs=True,
    )
    # [END howto_operator_k8s_private_image]

    # [START howto_operator_k8s_write_xcom]
    write_xcom = KubernetesPodOperator(
        namespace='default',
        image='alpine',
        cmds=["sh", "-c", "mkdir -p /airflow/xcom/;echo '[1,2,3,4]' > /airflow/xcom/return.json"],
        name="write-xcom",
        do_xcom_push=True,
        is_delete_operator_pod=True,
        in_cluster=True,
        task_id="write-xcom",
        get_logs=True,
    )

    pod_task_xcom_result = BashOperator(
        bash_command="echo \"{{ task_instance.xcom_pull('write-xcom')[0] }}\"",
        task_id="pod_task_xcom_result",
    )
    # [END howto_operator_k8s_write_xcom]

# from datetime import timedelta
#
# from airflow.kubernetes.pod import Resources
# from airflow.kubernetes.secret import Secret
# from airflow.models import DAG
# from airflow.operators.dummy_operator import DummyOperator
# # from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
# from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
# from airflow.utils.dates import days_ago
# from kubernetes.client import models as k8s
#
# ## ref: https://bomwo.cc/posts/kubernetespodoperator/
#
# dag_id = 'kubernetes-dag'
#
# task_default_args = {
#     'owner': 'Airflow',
#     'retries': 3,
#     'retry_delay': timedelta(minutes=5),
#     'start_date': days_ago(1),
#     'depends_on_past': False,
#     'email': ['ejpark@ncsoft.com'],
#     'email_on_retry': False,
#     'email_on_failure': False,
#     'execution_timeout': timedelta(hours=1)
# }
#
# dag = DAG(
#     dag_id=dag_id,
#     description='kubernetes pod operator',
#     default_args=task_default_args,
#     schedule_interval='5 16 * * *',
#     max_active_runs=1
# )
#
# env = Secret(
#     'env',
#     'TEST',
#     'test_env',
#     'TEST',
# )
#
# pod_resources = Resources()
# pod_resources.request_cpu = '200m'
# pod_resources.request_memory = '100Mi'
# pod_resources.limit_cpu = '200m'
# pod_resources.limit_memory = '100Mi'
#
# configmaps = [
#     k8s.V1EnvFromSource(config_map_ref=k8s.V1ConfigMapEnvSource(name='registry')),
# ]
#
# start = DummyOperator(task_id="start", dag=dag)
#
# run = KubernetesPodOperator(
#     task_id="kubernetespodoperator",
#     namespace='airflow',
#     image='registry.nlp-utils/crawler:dev',
#     secrets=[
#         env
#     ],
#     image_pull_secrets=[k8s.V1LocalObjectReference('registry')],
#     name="job",
#     is_delete_operator_pod=True,
#     get_logs=True,
#     resources=pod_resources,
#     env_from=configmaps,
#     dag=dag,
# )
#
# start >> run
