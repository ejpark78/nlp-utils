#!/usr/bin/env bash

SCRIPTS="crawler/web_news/web_news.py"

export PYTHONPATH=.
export ELASTIC_SEARCH_HOST="https://crawler-es.cloud.ncsoft.com:9200"
export ELASTIC_SEARCH_AUTH="elastic:searchT2020"


python3 ${SCRIPTS} --verbos 1 --sleep 2 --config config/mlbpark.yaml --list
