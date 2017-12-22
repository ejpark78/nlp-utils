#!/usr/bin/env bash

# 사전 위치 맵핑
home="hdfs://gollum:9000/user/"$(id -un)
archives="${home}/dictionary.jar#language_utils/dictionary,${home}/venv.jar#venv"

# home 위치: /user/root

# 경로 설정
#/usr/local/sbin/env.sh
export PATH=${HADOOP_HOME}/bin:${SPARK_HOME}/bin:.:$PATH
env

echo "libs 폴더 삭제"
hdfs dfs -rm -r -f -skipTrash libs

echo "import 되는 파일 업로드"
hdfs dfs -mkdir -p "${home}/libs"
hdfs dfs -put libs "${home}/"

# 실행
spark-submit \
    --packages "org.apache.spark:spark-streaming-kafka-0-8-assembly_2.11:2.0.2" \
    --conf "spark.yarn.dist.files=crawler/html_parser.py,crawler/utils.py,language_utils/keyword_extractor.py,language_utils/language_utils.py,language_utils/sp_utils/NCKmat.py,language_utils/sp_utils/NCSPProject.py" \
    --master yarn \
    --deploy-mode client \
    --archives "${archives}" \
    --num-executors 5 \
    --executor-cores 2 \
    --verbose \
    "spark_streaming.py"
