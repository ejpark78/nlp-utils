#!/usr/bin/env bash

set -x #echo on

config="/config/daum-news.yaml"

time bin/web_news.sh "--name daum-2017-04" --list --config ${config} --sleep 0.8 --date-range 2017-04-01
time bin/web_news.sh "--name daum-2017-03" --list --config ${config} --sleep 0.8 --date-range 2017-03-01
time bin/web_news.sh "--name daum-2017-02" --list --config ${config} --sleep 0.8 --date-range 2017-02-01
time bin/web_news.sh "--name daum-2017-01" --list --config ${config} --sleep 0.8 --date-range 2017-01-01
