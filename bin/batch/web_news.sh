#!/usr/bin/env bash

set -x #echo on

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"

time bin/web_news.sh "${config}" "--name contents-03" "--sleep 1.5 --contents --date-range 2021-03-01~2021-03-20"
