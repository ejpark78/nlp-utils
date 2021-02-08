from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator

configmaps = []

k = KubernetesPodOperator(
    namespace='airflow',
    image="registry.nlp-utils/crawler:dev",
    cmds=["bash", "-cx"],
    arguments=["echo", "10"],
    name="test",
    task_id="task",
    is_delete_operator_pod=True,
    hostnetwork=False,
    configmaps=configmaps
)

k
