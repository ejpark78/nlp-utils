#!/usr/bin/env bash

home="data/nate_baseball"

db_name="nate_baseball"

dry=""

for fname in $(ls -r ${home}/????.pos.bz2) ; do
    type_name=$(basename ${fname})
    type_name="${type_name/.parsed.bz2/}"

    echo ${fname}, ${db_name}, ${type_name}

    input_path=$(dirname ${fname})

    # 디비 입력
    input="${fname}"

    if [ "${dry}" == "" ] ; then
        time bzcat ${input} \
            | python3 NCElastic.py \
                -insert_documents \
                -es_host frodo \
                -index "${db_name}" \
                -type "${type_name}"
    fi
done

