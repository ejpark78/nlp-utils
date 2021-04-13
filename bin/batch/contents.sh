#!/usr/bin/env bash

set -x #echo on

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"

time bin/web_news.sh "--name contents-2021" --contents --config ${config} --sleep 1 --date-range 2021-01-01~2021-04-01

#time bin/web_news.sh "--name contents-2020-12" --contents --config ${config} --sleep 1 --date-range 2020-12-01~2020-12-01
#time bin/web_news.sh "--name contents-2020-11" --contents --config ${config} --sleep 1 --date-range 2020-11-01~2020-11-01
#time bin/web_news.sh "--name contents-2020-10" --contents --config ${config} --sleep 1 --date-range 2020-10-01~2020-10-01
#time bin/web_news.sh "--name contents-2020-09" --contents --config ${config} --sleep 1 --date-range 2020-09-01~2020-09-01
#time bin/web_news.sh "--name contents-2020-08" --contents --config ${config} --sleep 1 --date-range 2020-08-01~2020-08-01
#time bin/web_news.sh "--name contents-2020-07" --contents --config ${config} --sleep 1 --date-range 2020-07-01~2020-07-01
#time bin/web_news.sh "--name contents-2020-06" --contents --config ${config} --sleep 1 --date-range 2020-06-01~2020-06-01
#time bin/web_news.sh "--name contents-2020-05" --contents --config ${config} --sleep 1 --date-range 2020-05-01~2020-05-01
#time bin/web_news.sh "--name contents-2020-04" --contents --config ${config} --sleep 1 --date-range 2020-04-01~2020-04-01
#time bin/web_news.sh "--name contents-2020-03" --contents --config ${config} --sleep 1 --date-range 2020-03-01~2020-03-01
#time bin/web_news.sh "--name contents-2020-02" --contents --config ${config} --sleep 1 --date-range 2020-02-01~2020-02-01
#time bin/web_news.sh "--name contents-2020-01" --contents --config ${config} --sleep 1 --date-range 2020-01-01~2020-01-01
