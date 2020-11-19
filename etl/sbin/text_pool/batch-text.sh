#!/usr/bin/env bash

bin=$1
tag=$2
filename=$3
host_list=$4

python3 ${bin}/corpus_processor_client.py \
    -tag ${tag} \
    -filename ${filename} \
    -host_list ${host_list} \
    | 2> ${filename}.err.log
