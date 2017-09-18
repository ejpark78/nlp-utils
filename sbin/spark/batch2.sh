#!/usr/bin/env bash

# 실행

home="data/result"

for filename in $(ls -d ${home}/2017-0?-??.json.bz2) ; do
    echo ${filename}
    fname=$(basename ${filename})

    input="corpus/naver_economy/${fname}"
    output="data/result/by_date/${fname}"

    echo ${input}

    spark-submit \
        --master yarn \
        --deploy-mode client \
        --num-executors 15 \
        --executor-cores 4 \
        --verbose \
        SparkBatchSortByDate.py -filename ${input} -result ${output}

#    break
done


#input="corpus/naver_economy/2017-01.json.bz2"
#input="corpus/sample.json.bz2"

#        --driver-memory 32g \
#    --conf "spark.network.timeout=420000" \
#    --driver-memory 32g \
#    --spark.executor.memory 32g \
