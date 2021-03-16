#!/usr/bin/env bash

export PYTHONPATH=.
export ELASTIC_SEARCH_HOST="https://crawler-es.cloud.ncsoft.com:9200"
export ELASTIC_SEARCH_AUTH="elastic:searchT2020"
export CACHE_FILE="/tmp/crawler-es.size.json"

watch -d -n60 python3 crawler/utils/index_state.py --cache /tmp/crawler-es.size.json

#export ELASTIC_SEARCH_HOST="https://corpus.cloud.ncsoft.com:9200"
#export ELASTIC_SEARCH_AUTH="elastic:nlplab"
#export CACHE_FILE="/tmp/corpus.size.json"

#watch -d -n60 python3 crawler/utils/index_state.py --active
