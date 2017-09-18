#!/usr/bin/env bash

#job_name="test"
#max_map=75
#input="corpus/2017.pos.json.bz2"
#output="data/result/naver_economy-2017.pos.json.bz2"
#mapper="src/SplitByDate.py -extract_date"
#time ./sbin/hadoop/streaming.sh ${max_map} "${input}" "${output}" "${mapper}" "" "${job_name}"
#
#
#bzcat data/result/naver_economy-2017.pos.json.bz2 | SplitByDate.py -split_by_month



input="data/dump/2nd/naver_economy/2017.json.bz2"
output="data/dump/2nd/naver_economy/2017.by_month"

spark-submit \
    --master yarn \
    --deploy-mode client \
    --driver-memory 16g \
    --num-executors 9 \
    --executor-cores 1 \
    --verbose \
    SparkBatchSplitDate.py -filename ${input} -result ${output}


