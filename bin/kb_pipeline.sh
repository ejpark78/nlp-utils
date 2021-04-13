#!/usr/bin/env bash

set -x #echo on

docker_args="$1"
shift 1

image="registry.nlp-utils/crawler-dev:dev"

es_host="https://corpus.ncsoft.com:9200"
es_auth=$(echo -n "Y3Jhd2xlcjpjcmF3bGVyMjAxOQ==" | base64 -d)
db_auth=$(echo -n "cm9vdDpzZWFyY2hUMjAyMA==" | base64 -d)

docker run -it --rm \
  --network host \
  --add-host "corpus.ncsoft.com:172.20.93.112" \
  --add-host "crawler-mysql.cloud.ncsoft.com:172.19.154.164" \
  -e "ELASTIC_SEARCH_HOST=${es_host}" \
  -e "ELASTIC_SEARCH_AUTH=${es_auth}" \
  -e "ELASTIC_INDEX=crawler-naver-*-2021" \
  -e "DB_HOST=crawler-mysql.cloud.ncsoft.com" \
  -e "DB_AUTH=${db_auth}" \
  -e "DB_DATABASE=naver" \
  -e "DB_TABLE=naver" \
  -e "NLU_WRAPPER_URL=http://172.20.40.142" \
  ${docker_args} \
  ${image} \
    python3 -m crawler.web_news.pipeline $@
