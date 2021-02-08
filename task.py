from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.kubernetes.secret import Secret

secret_env = Secret('env', 'SQL_CONN', 'airflow-secrets', 'sql_alchemy_conn')

configmaps = []

k = KubernetesPodOperator(
    namespace='airflow',
    image="registry.nlp-utils/crawler:dev",
    cmds=["bash", "-cx"],
    arguments=["echo", "10"],
    labels={"foo": "bar"},
    secrets=[secret_env],
    name="test",
    task_id="task",
    is_delete_operator_pod=True,
    hostnetwork=False,
    configmaps=configmaps
)
