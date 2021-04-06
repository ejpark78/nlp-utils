#!/usr/bin/env bash

set -x #echo on

time bin/copy_raw_column.sh "--name copy-raw-col-2020" --index "crawler-naver-*-2020" --date-range 2020-01-01~2020-12-31
