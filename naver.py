from datetime import timedelta

from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago

dag = DAG(
    dag_id='naver',
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

start = DummyOperator(task_id='start', dag=dag)
end = DummyOperator(task_id='end', dag=dag)

category_list = {}
for task_id in 'economy,international,it,living,opinion,politics,society,sports,tv,weather'.split(','):
    category_list[task_id] = DummyOperator(task_id=task_id, dag=dag)

    start >> category_list[task_id]

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

sub_category = [
    {'category': 'economy', 'task_id': 'stock', 'name': "경제/증권", 'config': '/config/naver/economy.yaml'},
    {'category': 'economy', 'task_id': 'finance', 'name': "경제/금융", 'config': '/config/naver/economy.yaml'},
    {'category': 'economy', 'task_id': 'estate', 'name': "경제/부동산", 'config': '/config/naver/economy.yaml'},
    {'category': 'economy', 'task_id': 'industry', 'name': "경제/산업/재계", 'config': '/config/naver/economy.yaml'},
    {'category': 'economy', 'task_id': 'global', 'name': "경제/글로벌 경제", 'config': '/config/naver/economy.yaml'},
    {'category': 'economy', 'task_id': 'general', 'name': "경제/경제 일반", 'config': '/config/naver/economy.yaml'},
    {'category': 'economy', 'task_id': 'living', 'name': "경제/생활경제", 'config': '/config/naver/economy.yaml'},
    {'category': 'economy', 'task_id': 'venture', 'name': "경제/중기/벤처", 'config': '/config/naver/economy.yaml'},

    {'category': 'society', 'task_id': 'incident', 'name': "사회/사건사고", 'config': '/config/naver/society.yaml'},
    {'category': 'society', 'task_id': 'education', 'name': "사회/교육", 'config': '/config/naver/society.yaml'},
    {'category': 'society', 'task_id': 'labor', 'name': "사회/노동", 'config': '/config/naver/society.yaml'},
    {'category': 'society', 'task_id': 'media', 'name': "사회/언론", 'config': '/config/naver/society.yaml'},
    {'category': 'society', 'task_id': 'environment', 'name': "사회/환경", 'config': '/config/naver/society.yaml'},
    {'category': 'society', 'task_id': 'human-right', 'name': "사회/인권복지", 'config': '/config/naver/society.yaml'},
    {'category': 'society', 'task_id': 'medical', 'name': "사회/식품의료", 'config': '/config/naver/society.yaml'},
    {'category': 'society', 'task_id': 'local', 'name': "사회/지역", 'config': '/config/naver/society.yaml'},
    {'category': 'society', 'task_id': 'person', 'name': "사회/인물", 'config': '/config/naver/society.yaml'},
    {'category': 'society', 'task_id': 'etc', 'name': "사회/사회일반", 'config': '/config/naver/society.yaml'},

    {'category': 'weather', 'task_id': 'weather', 'name': "날씨", 'config': '/config/naver/weather.yaml'},

    {'category': 'sports', 'task_id': 'baseball', 'name': "스포츠/야구", 'config': '/config/naver/sports.yaml'},
    {'category': 'sports', 'task_id': 'wbaseball', 'name': "스포츠/해외야구", 'config': '/config/naver/sports.yaml'},
    {'category': 'sports', 'task_id': 'game', 'name': "스포츠/게임", 'config': '/config/naver/sports.yaml'},
    {'category': 'sports', 'task_id': 'football', 'name': "스포츠/축구", 'config': '/config/naver/sports.yaml'},
    {'category': 'sports', 'task_id': 'wfootball', 'name': "스포츠/해외축구", 'config': '/config/naver/sports.yaml'},
    {'category': 'sports', 'task_id': 'basketball', 'name': "스포츠/농구", 'config': '/config/naver/sports.yaml'},
    {'category': 'sports', 'task_id': 'volleyball', 'name': "스포츠/배구", 'config': '/config/naver/sports.yaml'},
    {'category': 'sports', 'task_id': 'golf', 'name': "스포츠/골프", 'config': '/config/naver/sports.yaml'},
    {'category': 'sports', 'task_id': 'etc', 'name': "스포츠/스포츠-일반", 'config': '/config/naver/sports.yaml'},
]

for item in sub_category:
    task = KubernetesPodOperator(
        dag=dag,
        name='app',
        task_id=item['task_id'],
        arguments=args + [
            '--config',
            item['config'],
            '--sub-category',
            item['name'],
        ],
        **params
    )

    category_list[item['category']] >> task >> end
