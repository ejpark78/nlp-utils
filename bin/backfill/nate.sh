#!/usr/bin/env bash

set -x #echo on

config="/config/nate-news.yaml"

#time bin/backfill.sh "${config}" "2021-03-01"
#time bin/backfill.sh "${config}" "2021-02-01"
#time bin/backfill.sh "${config}" "2021-01-01"

time bin/backfill.sh "${config}" "2019-12-01" "--name nate-12"
time bin/backfill.sh "${config}" "2019-11-01" "--name nate-11"
time bin/backfill.sh "${config}" "2019-10-01" "--name nate-10"
time bin/backfill.sh "${config}" "2019-09-01" "--name nate-09"
time bin/backfill.sh "${config}" "2019-08-01" "--name nate-08"
time bin/backfill.sh "${config}" "2019-07-01" "--name nate-07"
time bin/backfill.sh "${config}" "2019-06-01" "--name nate-06"
time bin/backfill.sh "${config}" "2019-05-01" "--name nate-05"
time bin/backfill.sh "${config}" "2019-04-01" "--name nate-04"
time bin/backfill.sh "${config}" "2019-03-01" "--name nate-03"
time bin/backfill.sh "${config}" "2019-02-01" "--name nate-02"
time bin/backfill.sh "${config}" "2019-01-01" "--name nate-01"
