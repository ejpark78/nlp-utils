#!/usr/bin/env bash

set -x #echo on

config="$1"
dt="$2"
docker_args="$3"
python_args="$4"

image="registry.nlp-utils/crawler-dev:dev"
es_host="https://crawler-es.cloud.ncsoft.com:9200"
es_auth=$(echo -n "ZWxhc3RpYzpzZWFyY2hUMjAyMA==" | base64 -d)

docker run -it --rm \
  --add-host "corpus.ncsoft.com:172.20.93.112" \
  --add-host "crawler-es.cloud.ncsoft.com:172.19.170.187" \
  -e "ELASTIC_SEARCH_HOST=${es_host}" \
  -e "ELASTIC_SEARCH_AUTH=${es_auth}" \
  ${docker_args} \
  ${image} \
    python3 -m crawler.web_news.web_news \
      --config "${config}" \
      --date-range "${dt}" \
      --sleep 0.8 \
      ${python_args} \
      --list
