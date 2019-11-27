#!/usr/bin/env bash

echo "python3 corpus_pipeline_utils.py \
    -nlu_domain baseball \
    -max_doc 50 \
    -max_core 24 \
    -timeout 32 \
    -source_index crawler-naver-sports-$1 \
    -target_index corpus_process-naver-sports-kbo-$1 \
    -source_host https://nlp.ncsoft.com:9200 \
    -target_host https://corpus.ncsoft.com:9200"


#cat index.list | xargs -l bash -c 'echo "python3 corpus_pipeline_utils.py \
#    -nlu_domain $0 \
#    -max_doc 50 \
#    -max_core 24 \
#    -timeout 32 \
#    -source_index crawler-naver-$1 \
#    -target_index corpus_process-naver-$1 \
#    -source_host https://nlp.ncsoft.com:9200 \
#    -target_host https://corpus.ncsoft.com:9200"'
