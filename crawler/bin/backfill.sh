#!/usr/bin/env bash

ARGS="--verbos 1 --sleep 0.8 --config config/naver-news.yaml,config/naver-news-sports.yaml --list"
SCRIPTS="crawler/web_news/web_news.py"

export PYTHONPATH=.
export ELASTIC_SEARCH_HOST="https://crawler-es.cloud.ncsoft.com:9200"
export ELASTIC_SEARCH_AUTH="elastic:searchT2020"


#python3 ${SCRIPTS} --date-range 2021-03-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2021-02-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2021-01-01 ${ARGS}


python3 ${SCRIPTS} --date-range 2020-12-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2020-11-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2020-10-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2020-09-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2020-08-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2020-07-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2020-06-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2020-05-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2020-04-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2020-03-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2020-02-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2020-01-01 ${ARGS}


python3 ${SCRIPTS} --date-range 2019-12-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2019-11-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2019-10-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2019-09-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2019-08-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2019-07-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2019-06-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2019-05-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2019-04-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2019-03-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2019-02-01 ${ARGS}
python3 ${SCRIPTS} --date-range 2019-01-01 ${ARGS}
