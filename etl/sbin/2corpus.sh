#!/usr/bin/env bash

# nlp -> corpus
cat index-2corpus.list | grep -v ^# | xargs -I{} echo "PYTHONPATH=. python3 utils/sync_elasticsearch.py \
    -sync_missing_doc \
    -source_index {} -target_index {} \
    -source_host https://crawler:crawler2019@nlp.ncsoft.com:9200 \
    -target_host https://crawler:crawler2019@corpus.ncsoft.com:9200" \
    | sh -
