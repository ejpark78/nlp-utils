
export AIRFLOW_HOME=$(pwd)/airflow
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT=$(pwd)
export AIRFLOW__KUBERNETES__GIT_DAGS_VOLUME_SUBPATH=dags
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/dags
#export AIRFLOW__CORE__EXECUTOR=KubernetesExecutor
#export AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@localhost/airflow
#export AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@localhost/airflow
#export KUBERNETES_SERVICE_HOST=172.19.168.82
#export KUBERNETES_SERVICE_PORT=6443
#export AIRFLOW__KUBERNETES__CONFIG_FILE=/home/ejpark/.kube/cluster.d/nc-crawler
#export KUBE_CONFIG=/home/ejpark/.kube/cluster.d/nc-crawler
#export KUBE_FILEPATH=/home/ejpark/.kube/cluster.d/nc-crawler
#export SERVICE_TOKEN_FILENAME=/home/ejpark/.kube/cluster.d/nc-crawler
#export AIRFLOW__KUBERNETES__IN_CLUSTER=false
#export AIRFLOW__WEBSERVER__DEFAULT_UI_TIMEZONE=Asia/Seoul
#export AIRFLOW__WEBSERVER__WORKER_REFRESH_BATCH_SIZE=8
#export AIRFLOW__WEBSERVER__WORKER_REFRESH_INTERVAL=60
#export AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=60
#export AIRFLOW__SCHEDULER__MAX_THREADS=8
#export AIRFLOW__SCHEDULER__RUN_DURATION=10800
#export AIRFLOW__SCHEDULER__SCHEDULER_HEALTH_CHECK_THRESHOLD=120
#export AIRFLOW__SCHEDULER__SCHEDULER_HEARTBEAT_SEC=60

rm airflow/airflow.db
airflow db init

#airflow users create \
#    --username admin \
#    --lastname 박 \
#    --firstname 은진 \
#    --role Admin \
#    --password searchT2020 \
#    --email ejpark@ncsoft.com

airflow webserver --port 8080
