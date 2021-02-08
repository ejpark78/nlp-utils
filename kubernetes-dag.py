from datetime import timedelta

from airflow.kubernetes.pod import Resources
from airflow.kubernetes.secret import Secret
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
# from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.utils.dates import days_ago
from kubernetes.client import models as k8s

## ref: https://bomwo.cc/posts/kubernetespodoperator/

dag_id = 'kubernetes-dag'

task_default_args = {
    'owner': 'Airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
    'depends_on_past': False,
    'email': ['ejpark@ncsoft.com'],
    'email_on_retry': False,
    'email_on_failure': False,
    'execution_timeout': timedelta(hours=1)
}

dag = DAG(
    dag_id=dag_id,
    description='kubernetes pod operator',
    default_args=task_default_args,
    schedule_interval='5 16 * * *',
    max_active_runs=1
)

env = Secret(
    'env',
    'TEST',
    'test_env',
    'TEST',
)

pod_resources = Resources()
pod_resources.request_cpu = '200m'
pod_resources.request_memory = '100Mi'
pod_resources.limit_cpu = '200m'
pod_resources.limit_memory = '100Mi'

configmaps = [
    k8s.V1EnvFromSource(config_map_ref=k8s.V1ConfigMapEnvSource(name='registry')),
]

start = DummyOperator(task_id="start", dag=dag)

run = KubernetesPodOperator(
    task_id="kubernetespodoperator",
    namespace='airflow',
    image='registry.nlp-utils/crawler:dev',
    secrets=[
        env
    ],
    image_pull_secrets=[k8s.V1LocalObjectReference('registry')],
    name="job",
    is_delete_operator_pod=True,
    get_logs=True,
    resources=pod_resources,
    env_from=configmaps,
    dag=dag,
)

start >> run
