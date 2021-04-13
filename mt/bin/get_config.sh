#!/usr/bin/env bash

set -x #echo on

host=$1
index=$2
doc_id=$3
user_auth=$4

curl -u ${user_auth} "${host}/${index}/_doc/${doc_id}?pretty" > config.json

cat config.json | jq ._source.batch | tee config.batch.json

# batch 변수 등록
$( cat config.json | jq ._source.batch | jq -r 'keys[] as $k | "export \($k)=\(.[$k])"' )

mkdir -p ${model_path}/config/

cp config.json ${model_path}/config/config.json

cat "${model_path}/config/config.json" | jq ._source.batch | tee "${model_path}/config/batch.json"
cat "${model_path}/config/config.json" | jq ._source.sync_model | tee "${model_path}/config/sync_model.json"
cat "${model_path}/config/config.json" | jq ._source.export_corpus | tee "${model_path}/config/export_corpus.json"
