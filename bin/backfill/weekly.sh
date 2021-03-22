#!/usr/bin/env bash

set -x #echo on

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"
time bin/backfill.sh "${config}" "2021-03-22~2021-03-31"

config="/config/nate-news.yaml"
time bin/backfill.sh "${config}" "2021-03-22~2021-03-31"

config="/config/daum-news.yaml"
time bin/backfill.sh "${config}" "2021-03-22~2021-03-31"
