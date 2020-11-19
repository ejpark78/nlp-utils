#!/usr/bin/env bash

f="$1"

#./batch.py -f "${f}" \
#    | ./elasticsearch_utils.py \
#        -import_data \
#        -host "http://corpus.ncsoft.com:9200" \
#        -index crawler-bbs-mlbpark_kbo
#
#rm "${f}"

PYTHONPATH=. python3 utils/nlu_wrapper_utils.py -filename ${f} > ${f}.out
