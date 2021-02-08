from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator

dag = DAG(
    dag_id='task',
    description='kubernetes pod operator',
    default_args={
        'owner': 'Airflow',
        'retries': 3,
        'depends_on_past': False,
        'email': ['ejpark@ncsoft.com'],
        'email_on_retry': False,
        'email_on_failure': False
    },
    schedule_interval='0,30 * * * *',
    max_active_runs=1
)

start = DummyOperator(task_id='start', dag=dag)

run = KubernetesPodOperator(
    namespace='airflow',
    image="registry.nlp-utils/crawler:dev",
    cmds=["bash", "-cx"],
    arguments=["echo", "10"],
    name="test",
    task_id="task",
    is_delete_operator_pod=True,
    hostnetwork=False,
    dag=dag,
)

start >> run
