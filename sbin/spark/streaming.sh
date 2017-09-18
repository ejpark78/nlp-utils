#!/usr/bin/env bash

# 사전 위치 맵핑
home="hdfs://master:9000/user/"$(id -un)
archives="${home}/dictionary.jar#dictionary"

# home 위치: /user/root

# 경로 설정
#/usr/local/sbin/env.sh
export PATH=${HADOOP_HOME}/bin:${SPARK_HOME}/bin:.:$PATH
env

# src 파일 삭제
hdfs dfs -rm -skipTrash src/*

# import 되는 파일을 hdfs 에 업로드
hdfs dfs -mkdir -p "${home}/src"
hdfs dfs -put *.py  "${home}/src/"
hdfs dfs -put *.ini "${home}/src/"
hdfs dfs -put *.so  "${home}/src/"

# 실행
spark-submit \
    --packages "org.apache.spark:spark-streaming-kafka-0-8-assembly_2.11:2.0.2" \
    --master yarn \
    --deploy-mode client \
    --archives "${archives}" \
    --num-executors 2 \
    --executor-cores 2 \
    --verbose \
    "SparkStreaming.py"
