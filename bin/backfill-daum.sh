#!/usr/bin/env bash

set -x #echo on

ARGS="--verbos 1 --sleep 0.8 --config config/daum-news.yaml --list"
SCRIPTS="-m crawler.web_news.web_news"

export PYTHONPATH=.
export ELASTIC_SEARCH_HOST="https://crawler-es.cloud.ncsoft.com:9200"
export ELASTIC_SEARCH_AUTH=$(echo ZWxhc3RpYzpzZWFyY2hUMjAyMA== | base64 -d)


YEAR=2021
#python3 ${SCRIPTS} --date-range ${YEAR}-03-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-02-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-01-01 ${ARGS}

#
#YEAR=2020
#python3 ${SCRIPTS} --date-range ${YEAR}-12-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-11-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-10-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-09-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-08-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-07-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-06-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-05-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-04-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-03-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-02-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-01-01 ${ARGS}
#
#
#YEAR=2019
#python3 ${SCRIPTS} --date-range ${YEAR}-12-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-11-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-10-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-09-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-08-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-07-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-06-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-05-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-04-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-03-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-02-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-01-01 ${ARGS}
