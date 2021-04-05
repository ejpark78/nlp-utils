

# crawler DAG 생성 

> airflow-web, airflow-scheduler POD 에는 git-sync 사이드카 컨테이너가 포함되어 있음.
> git-sync 는 주기적으로 dag 가 있는 git 저장소를 clone 함.
> 즉, dig git (http://galadriel02.korea.ncsoft.corp/crawler/airflow.git) 을 수정하면 일정시간 후 airflow 에 반영됨

## KubernetesPodOperator 예제

> 1.10.14 와 2.0.0 에서 KubernetesPodOperator 패키지 위치가 다름
> > 1.10.14: from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
> > 2.0.0: from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
> helm 은 1.10.14 까지 지원 

```python
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

start = DummyOperator(task_id='start', dag=dag)

run = KubernetesPodOperator(
    name='app',
    task_id='stock',
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
)

end = DummyOperator(task_id='end', dag=dag)

start >> run >> end
```

## DAG

```python
start >> category >> t1 >> t2 >> t3
```

```python
start >> category >> [t1, t2, t3]
```

```python
start >> category1 >> [c1-t1, c1-t2, c1-t3]
start >> category2 >> [c2-t1, c2-t2, c2-t3]
```

```python
start.set_downstream(task_or_task_list=t1)
```

```python
start.set_downstream(task_or_task_list=[t1, t2, t3])
```

## DAG Config 파일

```yaml
dag:
  dag_id: 'donga'
  description: 'donga crawler'
  schedule_interval: '10,40 * * * *'
  max_active_runs: 1
  concurrency: 64
  tags:
    - 국내 뉴스
    - 동아일보
default_args:
  owner: 'Airflow'
  retries: 3
  depends_on_past: False
  email:
    - ejpark@ncsoft.com
  email_on_retry: False
  email_on_failure: False
operator:
  params:
    labels:
      crawler: korea-news
    namespace: 'airflow'
    image: 'registry.nlp-utils/crawler:live'
    image_pull_policy: 'Always'
    image_pull_secrets: 'registry'
    is_delete_operator_pod: 'True'
    get_logs: 'True'
    cmds:
      - 'python3'
    env_vars:
      ELASTIC_SEARCH_HOST: 'https://corpus.ncsoft.com:9200'
      ELASTIC_SEARCH_AUTH: 'crawler:crawler2019'
  args:
    - -m
    - crawler.web_news.web_news
    - --sleep
    - '5'
    - --date-range
    - today
    - --mapping
    - /config/news/mapping.yaml
tasks:
  - category: Politics
    config: /config/news/donga.yaml
    name: Politics
    task_id: donga-Politics
  - category: Economy
    config: /config/news/donga.yaml
    name: Economy
    task_id: donga-Economy
  - category: Inter
    config: /config/news/donga.yaml
    name: Inter
    task_id: donga-Inter
  - category: Society
    config: /config/news/donga.yaml
    name: Society
    task_id: donga-Society
  - category: Culture
    config: /config/news/donga.yaml
    name: Culture
    task_id: donga-Culture
  - category: Entertainment
    config: /config/news/donga.yaml
    name: Entertainment
    task_id: donga-Entertainment
  - category: Sports
    config: /config/news/donga.yaml
    name: Sports
    task_id: donga-Sports
```

## CrawlerDagBuilder

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import timedelta
from os import getenv

import yaml
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.utils.dates import days_ago


class CrawlerDagBuilder(object):

    @staticmethod
    def open_config(filename: str) -> dict:
        path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT', '/opt/airflow/dags')
        sub_path = getenv('AIRFLOW__KUBERNETES__GIT_DAGS_VOLUME_SUBPATH', 'repo')

        filename = '{}/{}/{}'.format(path, sub_path, filename)

        with open(filename, 'r') as fp:
            data = yaml.load(stream=fp, Loader=yaml.FullLoader)
            return dict(data)

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

            task_group[name].append(KubernetesPodOperator(
                dag=dag,
                name='task',
                task_id=item['task_id'],
                arguments=config['operator']['args'] + extra_args,
                **config['operator']['params']
            ))

        return dag, task_group
```

## category 가 없는 dag: 카테고리별 동시 실행

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator

from crawler_dag_builder import CrawlerDagBuilder

filename = 'config/news/daejon.yaml'
dag, task_group = CrawlerDagBuilder().build(filename=filename)

start = DummyOperator(task_id='start', dag=dag)

prev = start
for name in task_group:
    for task in task_group[name]:
        prev.set_downstream(task_or_task_list=task)
        prev = task
```

## category 가 있는 dag: 순차 실행  

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator

from crawler_dag_builder import CrawlerDagBuilder

filename = 'config/portal/naver.yaml'
dag, task_group = CrawlerDagBuilder().build(filename=filename)

group_list = []
for name in task_group:
    grp = DummyOperator(task_id=name, dag=dag)
    grp.set_downstream(task_or_task_list=task_group[name])

    group_list.append(grp)

start = DummyOperator(task_id='start', dag=dag)
start.set_downstream(task_or_task_list=group_list)
```

## 간의 DAG 검증

### airflow web 실행

```bash
export AIRFLOW_HOME=$(pwd)/airflow
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT=$(pwd)
export AIRFLOW__KUBERNETES__GIT_DAGS_VOLUME_SUBPATH=./
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)

airflow initdb
airflow webserver --port 8080
```

### airflow dags report 

```bash
❯ airflow dags report
file                      | duration       | dag_num | task_num | dags          
==========================+================+=========+==========+===============
/bbs/bbs.py               | 0:00:00.006918 | 1       | 5        | bbs           
/crawler_dag_builder.py   | 0:00:00.003253 | 0       | 0        |               
/news/ajunews.py          | 0:00:00.015621 | 1       | 43       | ajunews       
/news/asiae.py            | 0:00:00.009116 | 1       | 22       | asiae         
/news/ccdailynews.py      | 0:00:00.005452 | 1       | 8        | ccdailynews   
/news/cctoday.py          | 0:00:00.005520 | 1       | 8        | cctoday       
/news/chosun-biz.py       | 0:00:00.006693 | 1       | 12       | chosun-biz    
/news/daejon.py           | 0:00:00.006620 | 1       | 12       | daejon        
/news/dailian.py          | 0:00:00.006394 | 1       | 11       | dailian       
/news/donga-cn.py         | 0:00:00.005739 | 1       | 9        | donga-cn      
/news/donga-en.py         | 0:00:00.005777 | 1       | 9        | donga-en      
/news/donga-jp.py         | 0:00:00.005785 | 1       | 9        | donga-jp      
/news/donga.py            | 0:00:00.005919 | 1       | 8        | donga         
/news/dt.py               | 0:00:00.006189 | 1       | 11       | dt            
/news/edaily.py           | 0:00:00.006620 | 1       | 12       | edaily        
/news/etnews.py           | 0:00:00.031309 | 1       | 10       | etnews        
/news/fnnews.py           | 0:00:00.013689 | 1       | 32       | fnnews        
/news/fntimes.py          | 0:00:00.005972 | 1       | 10       | fntimes       
/news/gyeonghyang.py      | 0:00:00.014528 | 1       | 41       | gyeonghyang   
/news/hani-cn.py          | 0:00:00.005966 | 1       | 10       | hani-cn       
/news/hani-en.py          | 0:00:00.005457 | 1       | 8        | hani-en       
/news/hani-jp.py          | 0:00:00.005506 | 1       | 8        | hani-jp       
/news/hani.py             | 0:00:00.029989 | 1       | 88       | hani          
/news/hankook.py          | 0:00:00.017966 | 1       | 54       | hankook       
/news/honam.py            | 0:00:00.014061 | 1       | 40       | honam         
/news/idaegu.py           | 0:00:00.007837 | 1       | 13       | idaegu        
/news/imaeil.py           | 0:00:00.017844 | 1       | 50       | imaeil        
/news/inews24.py          | 0:00:00.006784 | 1       | 10       | inews24       
/news/inews365.py         | 0:00:00.005978 | 1       | 9        | inews365      
/news/iusm.py             | 0:00:00.053074 | 0       | 0        |               
/news/jbdomin.py          | 0:00:00.033409 | 1       | 89       | jbdomin       
/news/jbnews.py           | 0:00:00.006941 | 1       | 12       | jbnews        
/news/jemin.py            | 0:00:00.028184 | 0       | 0        |               
/news/jjan.py             | 0:00:00.025438 | 1       | 69       | jjan          
/news/jnilbo.py           | 0:00:00.031872 | 1       | 91       | jnilbo        
/news/joins.py            | 0:00:00.006548 | 1       | 10       | joins         
/news/joongboo.py         | 0:00:00.005924 | 1       | 9        | joongboo      
/news/joongdo.py          | 0:00:00.037429 | 1       | 99       | joongdo       
/news/kjdaily.py          | 0:00:00.007011 | 1       | 13       | kjdaily       
/news/knnews.py           | 0:00:00.003318 | 1       | 2        | knnews        
/news/kookje.py           | 0:00:00.021172 | 0       | 0        |               
/news/ksilbo.py           | 0:00:00.003327 | 1       | 2        | ksilbo        
/news/kwangju.py          | 0:00:00.006046 | 1       | 10       | kwangju       
/news/kyeongin.py         | 0:00:00.008537 | 1       | 17       | kyeongin      
/news/newspeppermint.py   | 0:00:00.006396 | 1       | 11       | newspeppermint
/news/sbs-biz.py          | 0:00:00.005855 | 1       | 9        | sbs-biz       
/news/wowtv.py            | 0:00:00.005342 | 1       | 8        | wowtv         
/news/yeongnam.py         | 0:00:00.027975 | 1       | 88       | yeongnam      
/portal/daum.py           | 0:00:00.032857 | 1       | 86       | daum          
/portal/nate.py           | 0:00:00.025643 | 1       | 70       | nate          
/portal/naver.py          | 0:00:00.026649 | 1       | 71       | naver         
/portal/naver_kin.py      | 0:00:00.005154 | 1       | 5        | naver-kin     
/portal/naver_reply.py    | 0:00:00.007372 | 1       | 11       | naver-reply   
/world_news/47news.py     | 0:00:00.005809 | 1       | 9        | 47news        
/world_news/afp.py        | 0:00:00.003496 | 1       | 2        | afp           
/world_news/ansa.py       | 0:00:00.007061 | 1       | 20       | ansa          
/world_news/ap_news.py    | 0:00:00.009534 | 1       | 20       | ap_news       
/world_news/bbc.py        | 0:00:00.007037 | 1       | 21       | bbc           
/world_news/belga.py      | 0:00:00.003171 | 1       | 2        | belga         
/world_news/cna.py        | 0:00:00.007635 | 1       | 15       | cna           
/world_news/reuters-jp.py | 0:00:00.003624 | 1       | 3        | reuters-jp    
/world_news/reuters.py    | 0:00:00.005346 | 1       | 8        | reuters       
/world_news/tass.py       | 0:00:00.003926 | 1       | 4        | tass          
/world_news/upi.py        | 0:00:00.009424 | 1       | 27       | upi           
/world_news/xinhuanet.py  | 0:00:00.006070 | 1       | 14       | xinhuanet     
```
