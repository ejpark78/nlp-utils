#!/usr/bin/env bash

set -x #echo on

index="crawler-naver-*-2021"

time bin/copy_raw_column.sh "--name copy-raw-col-2021" --index ${index} --date-range 2021-01-01~2021-03-31
