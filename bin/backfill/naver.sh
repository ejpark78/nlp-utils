#!/usr/bin/env bash

set -x #echo on

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"

#time bin/backfill.sh "${config}" "2021-03-01"
#time bin/backfill.sh "${config}" "2021-02-01"
#time bin/backfill.sh "${config}" "2021-01-01"
#
#time bin/backfill.sh "${config}" "2020-12-01"
#time bin/backfill.sh "${config}" "2020-11-01"
#time bin/backfill.sh "${config}" "2020-10-01"
#time bin/backfill.sh "${config}" "2020-09-01"
#time bin/backfill.sh "${config}" "2020-08-01"
time bin/backfill.sh "${config}" "2020-07-01"
time bin/backfill.sh "${config}" "2020-06-01"
time bin/backfill.sh "${config}" "2020-05-01"
time bin/backfill.sh "${config}" "2020-04-01"
time bin/backfill.sh "${config}" "2020-03-01"
time bin/backfill.sh "${config}" "2020-02-01"
time bin/backfill.sh "${config}" "2020-01-01"
