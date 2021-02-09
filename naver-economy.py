from datetime import timedelta

from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago

dag = DAG(
    dag_id='naver-economy',
    description='kubernetes pod operator',
    default_args={
        'owner': 'Airflow',
        'retries': 3,
        'retry_delay': timedelta(minutes=10),
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

start = DummyOperator(task_id='start', dag=dag)

task1 = KubernetesPodOperator(
    dag=dag,
    name='app',
    task_id='stock',
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
    **params
)

task2 = KubernetesPodOperator(
    dag=dag,
    name='app',
    task_id='finance',
    arguments=[
        '-m',
        'crawler.web_news.web_news',
        '--sleep',
        '10',
        '--config',
        '/config/naver/economy.yaml',
        '--sub-category',
        '경제/금융',
    ],
    **params
)

end = DummyOperator(task_id='end', dag=dag)

start >> task1 >> end
start >> task2 >> end
