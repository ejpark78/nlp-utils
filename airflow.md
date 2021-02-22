# airflow

## local

* https://airflow.apache.org/docs/apache-airflow/stable/start/local.html

```bash
source venv/bin/activate

pip3 install -U -r requirements.dev.txt

export AIRFLOW_HOME=$(pwd)/airflow
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT=$(pwd) 
export AIRFLOW__KUBERNETES__GIT_DAGS_VOLUME_SUBPATH=dags 
export AIRFLOW_DAGS_FOLDER=$(pwd)/dags

rm airflow/airflow.db
airflow db init

airflow users create \
    --username admin \
    --lastname 박 \
    --firstname 은진 \
    --role Admin \
    --use-random-password \
    --email ejpark@ncsoft.com

airflow webserver --port 8080

airflow scheduler

airflow dags list
airflow dags report  
  
```

## docker

* https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.0.1/docker-compose.yaml'
```

* https://github.com/bitnami/bitnami-docker-airflow

```bash
curl -sSL https://raw.githubusercontent.com/bitnami/bitnami-docker-airflow/master/1/debian-10/docker-compose.yml > docker-compose.yml

docker-compose up -d
```

