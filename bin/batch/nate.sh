#!/usr/bin/env bash

set -x #echo on

config="/config/nate-news.yaml"

time bin/web_news.sh "--name nate-2018-04" --list --config ${config} --sleep 0.8 --date-range 2018-04-01
time bin/web_news.sh "--name nate-2018-03" --list --config ${config} --sleep 0.8 --date-range 2018-03-01
time bin/web_news.sh "--name nate-2018-02" --list --config ${config} --sleep 0.8 --date-range 2018-02-01
time bin/web_news.sh "--name nate-2018-01" --list --config ${config} --sleep 0.8 --date-range 2018-01-01

time bin/web_news.sh "--name nate-2017-12" --list --config ${config} --sleep 0.8 --date-range 2017-12-01
time bin/web_news.sh "--name nate-2017-11" --list --config ${config} --sleep 0.8 --date-range 2017-11-01
time bin/web_news.sh "--name nate-2017-10" --list --config ${config} --sleep 0.8 --date-range 2017-10-01
time bin/web_news.sh "--name nate-2017-09" --list --config ${config} --sleep 0.8 --date-range 2017-09-01
time bin/web_news.sh "--name nate-2017-08" --list --config ${config} --sleep 0.8 --date-range 2017-08-01
time bin/web_news.sh "--name nate-2017-07" --list --config ${config} --sleep 0.8 --date-range 2017-07-01
time bin/web_news.sh "--name nate-2017-06" --list --config ${config} --sleep 0.8 --date-range 2017-06-01
time bin/web_news.sh "--name nate-2017-05" --list --config ${config} --sleep 0.8 --date-range 2017-05-01
time bin/web_news.sh "--name nate-2017-04" --list --config ${config} --sleep 0.8 --date-range 2017-04-01
time bin/web_news.sh "--name nate-2017-03" --list --config ${config} --sleep 0.8 --date-range 2017-03-01
time bin/web_news.sh "--name nate-2017-02" --list --config ${config} --sleep 0.8 --date-range 2017-02-01
time bin/web_news.sh "--name nate-2017-01" --list --config ${config} --sleep 0.8 --date-range 2017-01-01
