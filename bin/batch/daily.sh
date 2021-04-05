#!/usr/bin/env bash

set -x #echo on

date_range=$(date +%Y-%m-%d --date "5 days ago")"~"$(date "+%Y-%m-%d")

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"
time bin/backfill.sh "${config}" "${date_range}" "--name naver-daily"

config="/config/nate-news.yaml"
time bin/backfill.sh "${config}" "${date_range}" "--name nate-daily"

config="/config/daum-news.yaml"
time bin/backfill.sh "${config}" "${date_range}" "--name daum-daily"
