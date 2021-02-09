from datetime import timedelta

from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago

dag = DAG(
    dag_id='naver',
    description='naver crawler',
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
]

start = DummyOperator(task_id='start', dag=dag)
end = DummyOperator(task_id='end', dag=dag)

category_list = {}
for task_id in 'economy,international,it,living,opinion,politics,society,sports,tv,weather'.split(','):
    category_list[task_id] = DummyOperator(task_id=task_id, dag=dag)

    start >> category_list[task_id]

sub_category = [
    {
        'category': 'economy',
        'task_id': 'stock',
        'name': '경제/증권',
    },
    {
        'category': 'economy',
        'task_id': 'finance',
        'name': '경제/금융',
    },
    {
        'category': 'economy',
        'task_id': 'estate',
        'name': '경제/부동산',
    },
    {
        'category': 'economy',
        'task_id': 'industry',
        'name': '경제/산업/재계',
    },
    {
        'category': 'economy',
        'task_id': 'global',
        'name': '경제/글로벌 경제',
    },
    {
        'category': 'economy',
        'task_id': 'general',
        'name': '경제/경제 일반',
    },
    {
        'category': 'economy',
        'task_id': 'economy-living',
        'name': '경제/생활경제',
    },
    {
        'category': 'economy',
        'task_id': 'venture',
        'name': '경제/중기/벤처',
    },

    {
        'category': 'international',
        'task_id': 'asia',
        'name': '세계/아시아호주',
    },
    {
        'category': 'international',
        'task_id': 'western',
        'name': '세계/미국중남미',
    },
    {
        'category': 'international',
        'task_id': 'europe',
        'name': '세계/유럽',
    },
    {
        'category': 'international',
        'task_id': 'mideast',
        'name': '세계/중동아프리카',
    },
    {
        'category': 'international',
        'task_id': 'international-etc',
        'name': '세계/일반',
    },

    {
        'category': 'it',
        'task_id': 'mobile',
        'name': 'IT/모바일',
    },
    {
        'category': 'it',
        'task_id': 'sns',
        'name': 'IT/인터넷/SNS',
    },
    {
        'category': 'it',
        'task_id': 'new-media',
        'name': 'IT/통신/뉴미디어',
    },
    {
        'category': 'it',
        'task_id': 'it-etc',
        'name': 'IT/IT 일반',
    },
    {
        'category': 'it',
        'task_id': 'security',
        'name': 'IT/보안/해킹',
    },
    {
        'category': 'it',
        'task_id': 'computer',
        'name': 'IT/컴퓨터',
    },
    {
        'category': 'it',
        'task_id': 'review',
        'name': 'IT/게임/리뷰',
    },
    {
        'category': 'it',
        'task_id': 'science',
        'name': 'IT/과학 일반',
    },

    {
        'category': 'living',
        'task_id': 'health',
        'name': '생활/건강정보',
    },
    {
        'category': 'living',
        'task_id': 'car',
        'name': '생활/자동차시승기',
    },
    {
        'category': 'living',
        'task_id': 'traffic',
        'name': '생활/도로교통',
    },
    {
        'category': 'living',
        'task_id': 'tour',
        'name': '생활/여행/레저',
    },
    {
        'category': 'living',
        'task_id': 'food',
        'name': '생활/음식맛집',
    },
    {
        'category': 'living',
        'task_id': 'beauty',
        'name': '생활/패션뷰티',
    },
    {
        'category': 'living',
        'task_id': 'art',
        'name': '생활/공연전시',
    },
    {
        'category': 'living',
        'task_id': 'book',
        'name': '생활/책',
    },
    {
        'category': 'living',
        'task_id': 'religion',
        'name': '생활/종교',
    },
    {
        'category': 'living',
        'task_id': 'living-forecast',
        'name': '생활/날씨',
    },
    {
        'category': 'living',
        'task_id': 'living-etc',
        'name': '생활/일반',
    },

    {
        'category': 'politics',
        'task_id': 'blue-house',
        'name': '정치/청와대',
    },
    {
        'category': 'politics',
        'task_id': 'national-assembly',
        'name': '정치/국회정당',
    },
    {
        'category': 'politics',
        'task_id': 'north-korea',
        'name': '정치/북한',
    },
    {
        'category': 'politics',
        'task_id': 'administration',
        'name': '정치/행정',
    },
    {
        'category': 'politics',
        'task_id': 'national-defense',
        'name': '정치/국방외교',
    },
    {
        'category': 'politics',
        'task_id': 'politics-etc',
        'name': '정치/정치일반',
    },

    {
        'category': 'society',
        'task_id': 'incident',
        'name': '사회/사건사고',
    },
    {
        'category': 'society',
        'task_id': 'education',
        'name': '사회/교육',
    },
    {
        'category': 'society',
        'task_id': 'labor',
        'name': '사회/노동',
    },
    {
        'category': 'society',
        'task_id': 'media',
        'name': '사회/언론',
    },
    {
        'category': 'society',
        'task_id': 'environment',
        'name': '사회/환경',
    },
    {
        'category': 'society',
        'task_id': 'human-right',
        'name': '사회/인권복지',
    },
    {
        'category': 'society',
        'task_id': 'medical',
        'name': '사회/식품의료',
    },
    {
        'category': 'society',
        'task_id': 'local',
        'name': '사회/지역',
    },
    {
        'category': 'society',
        'task_id': 'person',
        'name': '사회/인물',
    },
    {
        'category': 'society',
        'task_id': 'society-etc',
        'name': '사회/사회일반',
    },

    {
        'category': 'weather',
        'task_id': 'forecast',
        'name': '날씨',
    },
    {
        'category': 'opinion',
        'task_id': 'opi',
        'name': '날씨',
    },

    {
        'category': 'sports',
        'task_id': 'baseball',
        'name': '스포츠/야구',
    },
    {
        'category': 'sports',
        'task_id': 'wbaseball',
        'name': '스포츠/해외야구',
    },
    {
        'category': 'sports',
        'task_id': 'game',
        'name': '스포츠/게임',
    },
    {
        'category': 'sports',
        'task_id': 'football',
        'name': '스포츠/축구',
    },
    {
        'category': 'sports',
        'task_id': 'wfootball',
        'name': '스포츠/해외축구',
    },
    {
        'category': 'sports',
        'task_id': 'basketball',
        'name': '스포츠/농구',
    },
    {
        'category': 'sports',
        'task_id': 'volleyball',
        'name': '스포츠/배구',
    },
    {
        'category': 'sports',
        'task_id': 'golf',
        'name': '스포츠/골프',
    },
    {
        'category': 'sports',
        'task_id': 'sports-etc',
        'name': '스포츠/스포츠-일반',
    },
]

for item in sub_category:
    task = KubernetesPodOperator(
        dag=dag,
        name='task',
        task_id=item['task_id'],
        arguments=args + [
            '--config',
            '/config/naver/{}.yaml'.format(item['category']),
            '--sub-category',
            item['name'],
        ],
        **params
    )

    category_list[item['category']] >> task >> end
