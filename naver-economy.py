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

args = [
    '-m',
    'crawler.web_news.web_news',
    '--sleep',
    '10',
    '--config',
    '/config/naver/economy.yaml',
]

sub_category = [
    {'task_id': 'stock', 'name': "경제/증권"},
    {'task_id': 'finance', 'name': "경제/금융"},
    {'task_id': 'estate', 'name': "경제/부동산"},
    {'task_id': 'industry', 'name': "경제/산업/재계"},
    {'task_id': 'global', 'name': "경제/글로벌 경제"},
    {'task_id': 'general', 'name': "경제/경제 일반"},
    {'task_id': 'living', 'name': "경제/생활경제"},
    {'task_id': 'venture', 'name': "경제/중기/벤처"},
]

start = DummyOperator(task_id='start', dag=dag)

task_list = []
for item in sub_category:
    task = KubernetesPodOperator(
        dag=dag,
        name='app',
        task_id=item['task_id'],
        arguments=args + [
            '--sub-category',
            item['name'],
        ],
        **params
    )

    task_list.append(task)

end = DummyOperator(task_id='end', dag=dag)

for task in task_list:
    start >> task >> end
