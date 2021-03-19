#!/usr/bin/env bash

set -x #echo on

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"

time bin/backfill.sh "${config}" "2021-03-15~2021-03-31"
