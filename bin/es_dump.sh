#!/usr/bin/env bash

set -x #echo on

image="registry.nlp-utils/crawler:dev"
es_host="https://crawler-es.cloud.ncsoft.com:9200"
es_auth=$(echo -n "ZWxhc3RpYzpzZWFyY2hUMjAyMA==" | base64 -d)

dump_path=$(pwd)"/data/backfill"
mkdir -p "${dump_path}"

curl -k -s -u "${es_auth}" "${es_host}/_cat/indices?s=index&h=index,docs.count" \
  | grep -v "\." | tee "${dump_path}/index.list"

docker run -it --rm \
  --add-host "corpus.ncsoft.com:172.20.93.112" \
  --add-host "crawler-es.cloud.ncsoft.com:172.19.170.187" \
  -e "ELASTIC_SEARCH_HOST=${es_host}" \
  -e "ELASTIC_SEARCH_AUTH=${es_auth}" \
  -v "${dump_path}:/mnt" \
  ${image} \
    python3 -m crawler.utils.elasticsearch_utils \
      --dump --dump-path "/mnt" --index-list "/mnt/index.list"

sudo chown -R $(id -u):$(id -g) "${dump_path}"
