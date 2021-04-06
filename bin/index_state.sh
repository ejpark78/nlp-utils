#!/usr/bin/env bash

interval="$1"
es_server="$2"

shift 1
shift 1

cache_file="/tmp/index-state."$(dbus-uuidgen)".json"

if [[ ${es_server} == "corpus" ]]; then
  es_host="https://corpus.ncsoft.com:9200"
  es_auth=$(echo -n "ZWxhc3RpYzpubHBsYWI=" | base64 -d)
else
  es_host="https://crawler-es.cloud.ncsoft.com:9200"
  es_auth=$(echo -n "ZWxhc3RpYzpzZWFyY2hUMjAyMA==" | base64 -d)
fi

watch -d -n${interval} \
  python3 -m crawler.utils.index_state \
     --host "${es_host}" --auth "${es_auth}" \
     --index-size --cache "${cache_file}" $@
