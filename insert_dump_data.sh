#!/usr/bin/env bash

PYTHONPATH=. python3 module/crawler_corpus.py \
    -generate_cmd \
    -data_dir /home/ejpark/workspace/data-center/data/dump/mongodb/crawler/crawler.2019-03-18 \
    | grep naver | sort -r > 2019-03-18.sh

python3 crawler_corpus.py -generate_cmd -data_dir /home/ejpark/workspace/data-center/data/dump/mongodb/crawler/crawler.2019-01-28 | sort -r > 2019-01-28.sh

cluster green "docker pull registry.nlp-utils/crawler:latest"

parallel -j 10 -a mlbpark-kbo.sh
parallel -j 10 -a mlbpark-bullpen.sh
parallel -j 80 -a corpus.sh
parallel -j 20 -a new.sh

parallel -j 8 -a stop.sh



for id in $(docker ps --all --format "{{.ID}}" --filter "label=task=crawler_corpus"); do echo ${id}; docker logs ${id}; done


cluster green "docker ps --all --filter 'label=task=crawler_corpus'"

cluster green "docker ps --all"
cluster green "rm tmp/*.db"
cluster green "rm tmp/*.json.bz2"
cluster green "docker system prune -f"

cluster green "scp tmp/*.db koala:/home/ejpark/workspace/crawler/tmp/"

