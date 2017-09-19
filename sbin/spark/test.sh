#!/usr/bin/env bash


# https://arrow.apache.org/docs/python/filesystems.html
#export CLASSPATH=`$HADOOP_HOME/bin/hdfs classpath --glob`

#input="data/dump/2nd/naver_economy/2017.json.bz2"
input="data/sample.json.bz2"
output="/tmp/test"

hadoop fs -rm -r -f ${output}

spark-submit \
    --master yarn \
    --deploy-mode client \
    --driver-memory 16g \
    --num-executors 9 \
    --executor-cores 1 \
    --verbose \
    SparkBatchSplitDate.py -filename ${input} -result ${output}
