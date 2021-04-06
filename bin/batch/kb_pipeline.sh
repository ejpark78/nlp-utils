#!/usr/bin/env bash

set -x #echo on

time bin/kb_pipeline.sh "--name nlu-2021-03" --date-range 2021-03-01~2021-03-28
