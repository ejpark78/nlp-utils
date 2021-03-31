#!/usr/bin/env bash

set -x #echo on

name="mlbpark-kbo"
config="/config/mlbpark.yaml"

image="registry.nlp-utils/crawler:dev"
es_host="https://crawler-es.cloud.ncsoft.com:9200"
es_auth=$(echo -n "ZWxhc3RpYzpzZWFyY2hUMjAyMA==" | base64 -d)

docker run -it --rm \
  --add-host "corpus.ncsoft.com:172.20.93.112" \
  --add-host "crawler-es.cloud.ncsoft.com:172.19.170.187" \
  -e "ELASTIC_SEARCH_HOST=${es_host}" \
  -e "ELASTIC_SEARCH_AUTH=${es_auth}" \
  --name "${name}" \
  ${image} \
    python3 -m crawler.web_news.web_news \
      --config "${config}" \
      --sleep 5 \
      --job-name "bullpen" \
      --page-range "326251~9000000" \
      --list
