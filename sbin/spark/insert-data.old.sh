#!/usr/bin/env bash

# 실행

home="data/mlbpark/kbo"

#host_name="gollum"
host_name="frodo01"
port="27018"
prefix="mlbpark_kbo"

for section in $(\ls -d ${home}/*/) ; do
    section=$(basename ${section})
    db_name=${prefix}"_"${section}

    echo
    echo ${section} ${db_name}

    for fname in $(\ls -r ${home}/${section}/????.by_month/????-??.bz2) ; do
        collection=$(basename ${fname})
        collection="${collection/.json/}"
        collection="${collection/.bz2/}"

        echo ${fname}, ${db_name}, ${collection}

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
    done
done

sync

mongodump -j 20 --gzip --archive=${prefix}.archive

