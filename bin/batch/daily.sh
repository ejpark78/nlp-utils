#!/usr/bin/env bash

set -x #echo on

date_range=$(date +%Y-%m-%d --date "1 days ago")"~"$(date "+%Y-%m-%d")

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"
time bin/web_news.sh  "--name naver-daily" --list --config ${config} --sleep 0.8 --date-range ${date_range}

config="/config/nate-news.yaml"
time bin/web_news.sh  "--name nate-daily" --list --config ${config} --sleep 0.8 --date-range ${date_range}

config="/config/daum-news.yaml"
time bin/web_news.sh  "--name daum-daily" --list --config ${config} --sleep 0.8 --date-range ${date_range}
