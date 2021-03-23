#!/usr/bin/env bash

set -x #echo on

date_range=$(date +%Y-%m-%d --date "2 days ago")"~"$(date "+%Y-%m-%d")

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"
time bin/backfill.sh "${config}" "${date_range}"

config="/config/nate-news.yaml"
time bin/backfill.sh "${config}" "${date_range}"

config="/config/daum-news.yaml"
time bin/backfill.sh "${config}" "${date_range}"
