#!/usr/bin/env bash

# 실행

home="data/dump/2nd"

for dir_name in $(ls -d ${home}/*/) ; do
    echo ${dir_name}
    db_name=$(basename ${dir_name})

    for filename in $(ls ${home}/${db_name}/2017.json.bz2) ; do
        if [ ! -f ${filename} ] ; then
            continue
        fi

        echo ${db_name} ${filename}
        fname=$(basename ${filename})
        year="${fname/.json.bz2/}"

        input="corpus/news/2nd/${db_name}/${fname}"

        echo ${db_name}, ${input}

        spark-submit \
            --master yarn \
            --deploy-mode client \
            --num-executors 15 \
            --executor-cores 4 \
            --verbose \
            SparkBatch.py -db_name ${db_name} -filename ${input}
    done
done


#    --total-executor-cores 90 \
