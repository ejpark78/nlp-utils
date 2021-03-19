#!/usr/bin/env bash

set -x #echo on

config="/config/naver-news.yaml,/config/naver-news-sports.yaml"

time bin/backfill.sh "${config}" "2021-03-15~2021-03-31"

year=2020
time bin/backfill.sh "${config}" "${year}-12-01"
time bin/backfill.sh "${config}" "${year}-11-01"
time bin/backfill.sh "${config}" "${year}-10-01"
time bin/backfill.sh "${config}" "${year}-09-01"
time bin/backfill.sh "${config}" "${year}-08-01"
time bin/backfill.sh "${config}" "${year}-07-01"
time bin/backfill.sh "${config}" "${year}-06-01"
time bin/backfill.sh "${config}" "${year}-05-01"
time bin/backfill.sh "${config}" "${year}-04-01"
time bin/backfill.sh "${config}" "${year}-03-01"
time bin/backfill.sh "${config}" "${year}-02-01"
time bin/backfill.sh "${config}" "${year}-01-01"
