#!/usr/bin/env bash

set -x #echo on

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"

time bin/web_news.sh "--name naver-2016-12" --list --config ${config} --sleep 0.8 --date-range 2016-12-01
time bin/web_news.sh "--name naver-2016-11" --list --config ${config} --sleep 0.8 --date-range 2016-11-01
time bin/web_news.sh "--name naver-2016-10" --list --config ${config} --sleep 0.8 --date-range 2016-10-01
time bin/web_news.sh "--name naver-2016-09" --list --config ${config} --sleep 0.8 --date-range 2016-09-01
time bin/web_news.sh "--name naver-2016-08" --list --config ${config} --sleep 0.8 --date-range 2016-08-01
time bin/web_news.sh "--name naver-2016-07" --list --config ${config} --sleep 0.8 --date-range 2016-07-01
time bin/web_news.sh "--name naver-2016-06" --list --config ${config} --sleep 0.8 --date-range 2016-06-01
time bin/web_news.sh "--name naver-2016-05" --list --config ${config} --sleep 0.8 --date-range 2016-05-01
time bin/web_news.sh "--name naver-2016-04" --list --config ${config} --sleep 0.8 --date-range 2016-04-01
time bin/web_news.sh "--name naver-2016-03" --list --config ${config} --sleep 0.8 --date-range 2016-03-01
time bin/web_news.sh "--name naver-2016-02" --list --config ${config} --sleep 0.8 --date-range 2016-02-01
time bin/web_news.sh "--name naver-2016-01" --list --config ${config} --sleep 0.8 --date-range 2016-01-01

time bin/web_news.sh "--name naver-2015-12" --list --config ${config} --sleep 0.8 --date-range 2015-12-01
time bin/web_news.sh "--name naver-2015-11" --list --config ${config} --sleep 0.8 --date-range 2015-11-01
time bin/web_news.sh "--name naver-2015-10" --list --config ${config} --sleep 0.8 --date-range 2015-10-01
time bin/web_news.sh "--name naver-2015-09" --list --config ${config} --sleep 0.8 --date-range 2015-09-01
time bin/web_news.sh "--name naver-2015-08" --list --config ${config} --sleep 0.8 --date-range 2015-08-01
time bin/web_news.sh "--name naver-2015-07" --list --config ${config} --sleep 0.8 --date-range 2015-07-01
time bin/web_news.sh "--name naver-2015-06" --list --config ${config} --sleep 0.8 --date-range 2015-06-01
time bin/web_news.sh "--name naver-2015-05" --list --config ${config} --sleep 0.8 --date-range 2015-05-01
time bin/web_news.sh "--name naver-2015-04" --list --config ${config} --sleep 0.8 --date-range 2015-04-01
time bin/web_news.sh "--name naver-2015-03" --list --config ${config} --sleep 0.8 --date-range 2015-03-01
time bin/web_news.sh "--name naver-2015-02" --list --config ${config} --sleep 0.8 --date-range 2015-02-01
time bin/web_news.sh "--name naver-2015-01" --list --config ${config} --sleep 0.8 --date-range 2015-01-01
