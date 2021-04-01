#!/usr/bin/env bash

set -x #echo on

index="crawler-naver-*-2021"

time bin/fill_raw.sh "${index}" "2021-03-01~2021-03-10"
time bin/fill_raw.sh "${index}" "2021-03-10~2021-03-20"
time bin/fill_raw.sh "${index}" "2021-03-20~2021-03-30"
