#!/usr/bin/env bash

set -x #echo on

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"

time bin/web_news.sh "--name contents-2021-03" "--contents --config ${config} --sleep 1.5 --date-range 2021-01-01~2021-04-01"
