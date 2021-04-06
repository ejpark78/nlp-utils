#!/usr/bin/env bash

set -x #echo on

config="/config/mlbpark.yaml"
time bin/web_news.sh "--name mlbpark-bullpen" --list --config ${config} --sleep 5 --job-name "bullpen" --page-range "1559101~9000000"
