#!/usr/bin/env bash

interval="$1"
es_server="$2"

SCRIPTS="-m crawler.utils.index_state"
#SCRIPTS="crawler/utils/index_state.py"

export PYTHONPATH=.

cache_file="/tmp/index-state."$(dbus-uuidgen)".json"

if [[ ${es_server} == "corpus" ]]; then
  host="https://corpus.ncsoft.com:9200"
  auth=$(echo -n "ZWxhc3RpYzpubHBsYWI=" | base64 -d)
else
  host="https://crawler-es.cloud.ncsoft.com:9200"
  auth=$(echo -n "ZWxhc3RpYzpzZWFyY2hUMjAyMA==" | base64 -d)
fi

watch -d -n${interval} \
  python3 ${SCRIPTS} --active --cache "${cache_file}" --host "${host}" --auth "${auth}"
