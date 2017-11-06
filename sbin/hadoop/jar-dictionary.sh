#!/usr/bin/env bash

echo -e "\n사전 압축: dictionary.jar"

#jar cvf dictionary.jar -C dictionary/ .


echo -e "\nvenv 압축: venv.jar"
jar cvf venv.jar -C venv/ .

#hdfs dfs -rm -skipTrash "${home}/dictionary.jar"
#hdfs dfs -put dictionary.jar ${home}/
