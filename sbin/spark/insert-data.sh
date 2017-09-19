#!/usr/bin/env bash

# 실행

home="data/dump/2nd"

for dir_name in $(ls -d ${home}/nate_*) ; do
    db_name=$(basename ${dir_name})

    for fname in $(ls ${home}/${db_name}/*.by_month/2017-09.bz2) ; do
        collection=$(basename ${fname})
        collection="${collection/.bz2/}"

        echo ${fname}, ${db_name}, ${collection}

        bzcat ${fname} | mongoimport --host gollum --port 37017 --db ${db_name} --collection ${collection} --upsert --numInsertionWorkers 7
    done
done

