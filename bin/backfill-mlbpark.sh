#!/usr/bin/env bash

set -x #echo on

SCRIPTS="-m crawler.web_news.web_news"

export PYTHONPATH=.
export ELASTIC_SEARCH_HOST="https://crawler-es.cloud.ncsoft.com:9200"
export ELASTIC_SEARCH_AUTH=$(echo ZWxhc3RpYzpzZWFyY2hUMjAyMA== | base64 -d)


python3 ${SCRIPTS} --verbos 1 --sleep 2 --config config/mlbpark.yaml --list
