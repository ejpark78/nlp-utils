#!/usr/bin/env bash

set -x #echo on

ARGS="--verbos 2 --sleep 0.8 --config config/naver-news.yaml,config/naver-news-sports.yaml --list"
SCRIPTS="-m crawler.web_news.web_news"

export PYTHONPATH=.
export ELASTIC_SEARCH_HOST="https://crawler-es.cloud.ncsoft.com:9200"
export ELASTIC_SEARCH_AUTH=$(echo ZWxhc3RpYzpzZWFyY2hUMjAyMA== | base64 -d)


YEAR=2021

docker run -it --rm \
		--add-host "corpus.ncsoft.com:172.20.93.112" \
		-e "ELASTIC_SEARCH_HOST=https://corpus.ncsoft.com:9200" \
		-e "ELASTIC_SEARCH_AUTH=crawler:crawler2019" \
		$(IMAGE):dev \
			python3 -m crawler.web_news.web_news \
				--sleep 10 \
				--config /config/naver-news.yaml \
				--job-name economy \
				--sub-category "경제/증권"

python3 ${SCRIPTS} --date-range ${YEAR}-03-15~${YEAR}-03-31 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-03-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-02-01 ${ARGS}
#python3 ${SCRIPTS} --date-range ${YEAR}-01-01 ${ARGS}


YEAR=2020
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

