from datetime import datetime, timedelta

from airflow import models
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator

with models.DAG('dag_node_pool',
                schedule_interval=timedelta(minutes=1),
                start_date=datetime(2019, 10, 3, 0, 0, 0),
                catchup=False) as dag:
    # namespace, name 은 필수.
    # 잘 모르겠으니 namespace 는 'default' 로 하고, name 은 task_id 와 동일하게.
    node_pool_test = KubernetesPodOperator(
        task_id='node-pool-test',
        namespace='default',
        image='bash',
        name='node-pool-test',
        cmds=['echo', 'fakenerd']
    )
