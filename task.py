from datetime import timedelta

from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago

## ref: https://bomwo.cc/posts/kubernetespodoperator/
## https://stackoverflow.com/questions/56296775/airflow-modulenotfounderror-no-module-named-kubernetes

dag = DAG(
    dag_id='task',
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

start = DummyOperator(task_id='start', dag=dag)

run = KubernetesPodOperator(
    name="job",
    task_id="task",
    namespace='airflow',
    image='registry.nlp-utils/crawler:dev',
    is_delete_operator_pod=True,
    image_pull_secrets='registry',
    get_logs=True,
    dag=dag,
)

end = DummyOperator(task_id='end', dag=dag)

start >> run >> end
