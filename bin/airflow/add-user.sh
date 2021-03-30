#!/usr/bin/env bash

export AIRFLOW_HOME="$(pwd)/airflow"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/dags"

airflow users create \
    --username admin \
    --lastname 박 \
    --firstname 은진 \
    --role Admin \
    --password searchT2020 \
    --email ejpark@ncsoft.com
