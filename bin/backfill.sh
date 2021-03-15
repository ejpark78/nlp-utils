#!/usr/bin/env bash

ARGS="--verbos 1 --sleep 0.8 --config config/naver-news.yaml,config/naver-news-sports.yaml --list"
SCRIPTS="crawler/web_news/web_news.py"

export PYTHONPATH=.
export ELASTIC_SEARCH_HOST="https://crawler-es.cloud.ncsoft.com:9200"
export ELASTIC_SEARCH_AUTH="elastic:searchT2020"


YEAR=2021
#python3 ${SCRIPTS} --date-range ${YEAR}-03-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-02-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-01-01 ${ARGS}


YEAR=2020
python3 ${SCRIPTS} --date-range ${YEAR}-12-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-11-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-10-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-09-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-08-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-07-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-06-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-05-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-04-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-03-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-02-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-01-01 ${ARGS}


YEAR=2019
python3 ${SCRIPTS} --date-range ${YEAR}-12-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-11-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-10-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-09-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-08-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-07-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-06-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-05-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-04-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-03-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-02-01 ${ARGS}
python3 ${SCRIPTS} --date-range ${YEAR}-01-01 ${ARGS}
