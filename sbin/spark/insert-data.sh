#!/usr/bin/env bash

# 실행

home="data/nate/baseball"

host_name="frodo"
port="27017"
db_name="nate_baseball"

dry=""

for fname in $(\ls -r ${home}/????.by_month/????-??.parsed.bz2) ; do
    collection=$(basename ${fname})
    collection="${collection/.pos/}"
    collection="${collection/.parsed/}"
    collection="${collection/.json/}"
    collection="${collection/.bz2/}"

    echo ${fname}, ${db_name}, ${collection}

    if [ "${dry}" == "" ] ; then
        bzcat ${fname} \
            | mongoimport \
                --host ${host_name} \
                --port ${port} \
                --db ${db_name} \
                --collection ${collection} \
                --mode=insert \
                --verbose=2 \
                --numInsertionWorkers $(nproc) \
                --writeConcern '{w: 1, wtimeout: 50000, j: false}'
    fi
done

