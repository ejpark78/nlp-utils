#!/usr/bin/env bash

set -x #echo on

index="crawler-naver-*-2021"

time bin/fill_raw.sh "${index}" "2021-03-01~2021-03-10" "--name fill-raw-0310"
time bin/fill_raw.sh "${index}" "2021-03-10~2021-03-20" "--name fill-raw-0320"
time bin/fill_raw.sh "${index}" "2021-03-20~2021-03-30" "--name fill-raw-0330"

time bin/fill_raw.sh "${index}" "2021-02-01~2021-02-10" "--name fill-raw-0210"
time bin/fill_raw.sh "${index}" "2021-02-10~2021-02-20" "--name fill-raw-0220"
time bin/fill_raw.sh "${index}" "2021-02-20~2021-03-01" "--name fill-raw-0230"

time bin/fill_raw.sh "${index}" "2021-01-01~2021-01-10" "--name fill-raw-0110"
time bin/fill_raw.sh "${index}" "2021-01-10~2021-01-20" "--name fill-raw-0120"
time bin/fill_raw.sh "${index}" "2021-01-20~2021-02-01" "--name fill-raw-0130"
