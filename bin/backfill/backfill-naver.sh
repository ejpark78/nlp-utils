#!/usr/bin/env bash

set -x #echo on

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"

time bin/backfill.sh "${config}" "2021-01-01~2021-03-31"
time bin/backfill.sh "${config}" "2020-01-01~2020-12-31"
