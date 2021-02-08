from datetime import timedelta

from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from kubernetes.client.models import V1Container
from airflow.kubernetes.volume_mount import VolumeMount
## ref: https://bomwo.cc/posts/kubernetespodoperator/
## https://stackoverflow.com/questions/56296775/airflow-modulenotfounderror-no-module-named-kubernetes

dag = DAG(
    dag_id='crawler',
    description='kubernetes pod operator',
    default_args={
        'owner': 'Airflow',
        'retries': 3,
        'retry_delay': timedelta(minutes=5),
        'start_date': days_ago(1),
        'depends_on_past': False,
        'email': ['ejpark@ncsoft.com'],
        'email_on_retry': False,
        'email_on_failure': False,
        'execution_timeout': timedelta(hours=1)
    },
    schedule_interval='0,30 * * * *',
    max_active_runs=1
)

init_container = V1Container(
    command=['git'],
    args=[
        'clone',
        '--progress',
        '-b',
        '$(GIT_SYNC_BRANCH)',
        '$(GIT_SYNC_REPO)',
        '/config',
    ],
    env={
        'GIT_SYNC_REPO': 'http://172.20.92.245/crawler/config.git',
        'GIT_SYNC_BRANCH': 'live',
    },
    image='registry.nlp-utils/alpine/git:v2.30.0',
    image_pull_policy='IfNotPresent',
    name='git-sync',
    volume_devices=None,
    volume_mounts=[VolumeMount('config', mount_path='/config', sub_path=None, read_only=False)],
)

start = DummyOperator(task_id='start', dag=dag)

run = KubernetesPodOperator(
    name='economy',
    task_id='naver',
    namespace='airflow',
    image='registry.nlp-utils/crawler:live',
    is_delete_operator_pod=False,
    image_pull_policy='Always',
    image_pull_secrets='registry',
    env_vars={
        'ELASTIC_SEARCH_HOST': 'https://corpus.ncsoft.com:9200',
        'ELASTIC_SEARCH_AUTH': 'crawler:crawler2019',
    },
    get_logs=True,
    dag=dag,
    cmds=['python3'],
    arguments=[
        '-m',
        'crawler.web_news.web_news',
        '--sleep',
        '10',
        '--config',
        '/config/naver/economy.yaml',
        '--sub-category',
        '경제/증권',
    ],
    init_containers=[init_container],
    volume_mounts=[VolumeMount('config', mount_path='/config', sub_path=None, read_only=False)],
)

end = DummyOperator(task_id='end', dag=dag)

start >> run >> end
