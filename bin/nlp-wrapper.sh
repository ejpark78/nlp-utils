#!/usr/bin/env bash

set -x #echo on

dt_range="$1"
docker_args="$2"

image="registry.nlp-utils/crawler:dev"
es_host="https://crawler-es.cloud.ncsoft.com:9200"
es_auth=$(echo -n "ZWxhc3RpYzpzZWFyY2hUMjAyMA==" | base64 -d)
db_passwd=$(echo -n "c2VhcmNoVDIwMjA=" | base64 -d)

docker run -it --rm \
  --add-host "corpus.ncsoft.com:172.20.93.112" \
  --add-host "crawler-es.cloud.ncsoft.com:172.19.170.187" \
  -e "ELASTIC_SEARCH_HOST=${es_host}" \
  -e "ELASTIC_SEARCH_AUTH=${es_auth}" \
  -e "ELASTIC_INDEX=crawler-naver-*-2021" \
  -e "DB_HOST=crawler-mysql.cloud.ncsoft.com" \
  -e "DB_USER=root" \
  -e "DB_PASSWORD=${db_passwd}" \
  -e "DB_DATABASE=naver" \
  -e "DB_TABLE=naver" \
  -e "NLU_WRAPPER_URL=http://172.20.40.142" \
  ${docker_args} \
  ${image} \
    python3 -m crawler.utils.nlu_wrapper \
      --date-range "${dt_range}"
