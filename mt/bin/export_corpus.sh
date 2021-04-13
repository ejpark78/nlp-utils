#!/usr/bin/env bash

set -x #echo on

src="$1"
trg="$2"
column_src="$3"
column_trg="$4"
model_path="$5"

# export bitext corpus
python3 bin/export_corpus.py \
    --export=true \
    --config="${model_path}/config/export_corpus.json" \
    | bzip2 - > "${model_path}/corpus.json.bz2"
sync

bzcat "${model_path}/corpus.json.bz2" \
    | jq -r ".${column_src},.${column_trg}" \
    | paste - - > "${model_path}/train.${src}-${trg}"
sync

cut -f1 "${model_path}/train.${src}-${trg}" > "${model_path}/train.${src}"
cut -f2 "${model_path}/train.${src}-${trg}" > "${model_path}/train.${trg}"
sync

wc -l "${model_path}/train.${src}-${trg}" "${model_path}/train.${src}" "${model_path}/train.${trg}"
