#!/usr/bin/env bash

set -x #echo on

config="/config/daum-news.yaml"

#time bin/backfill.sh "${config}" "2021-03-01"
#time bin/backfill.sh "${config}" "2021-02-01"
#time bin/backfill.sh "${config}" "2021-01-01"
#
#time bin/backfill.sh "${config}" "2020-12-01" "--name daum-12"
#time bin/backfill.sh "${config}" "2020-11-01" "--name daum-11"
#time bin/backfill.sh "${config}" "2020-10-01" "--name daum-10"
#time bin/backfill.sh "${config}" "2020-09-01" "--name daum-09"
#time bin/backfill.sh "${config}" "2020-08-01" "--name daum-08"
time bin/backfill.sh "${config}" "2020-07-01" "--name daum-07"
time bin/backfill.sh "${config}" "2020-06-01" "--name daum-06"
time bin/backfill.sh "${config}" "2020-05-01" "--name daum-05"
time bin/backfill.sh "${config}" "2020-04-01" "--name daum-04"
time bin/backfill.sh "${config}" "2020-03-01" "--name daum-03"
time bin/backfill.sh "${config}" "2020-02-01" "--name daum-02"
time bin/backfill.sh "${config}" "2020-01-01" "--name daum-01"
