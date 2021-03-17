#!/usr/bin/env bash

PYTHONPATH=.
ELASTIC_SEARCH_HOST="https://crawler-es.cloud.ncsoft.com:9200"
ELASTIC_SEARCH_AUTH=$(echo ZWxhc3RpYzpzZWFyY2hUMjAyMA== | base64 -d)

DUMP_PATH="data/naver-backfill"
mkdir -p ${DUMP_PATH}

curl -k -s -u ${ELASTIC_SEARCH_AUTH} "${ELASTIC_SEARCH_HOST}/_cat/indices?s=index&h=index,docs.count" \
  | grep -v "\." | tee ${DUMP_PATH}/index.list

python3 crawler/utils/elasticsearch_utils.py \
  --dump \
  --dump-path ${DUMP_PATH} \
  --index-list ${DUMP_PATH}/index.list
