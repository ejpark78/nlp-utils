#!/usr/bin/env bash

set -x #echo on

docker_args="$1"
shift 1

image="registry.nlp-utils/crawler-dev:dev"

docker run -it --rm \
  --add-host "corpus.ncsoft.com:172.20.93.112" \
  --add-host "crawler-es.cloud.ncsoft.com:172.19.170.187" \
  ${docker_args} \
  ${image} \
    python3 -m crawler.web_news.backfill $@
