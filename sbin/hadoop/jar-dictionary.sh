#!/usr/bin/env bash

echo -e "\n사전 압축: dictionary.jar"

#jar cvf dictionary.jar -C dictionary/ .


echo -e "\nvenv 압축: venv.jar"

#hdfs dfs -rm -skipTrash "${home}/dictionary.jar"
#hdfs dfs -put dictionary.jar ${home}/

jar cvf venv.jar -C venv/ .
jar cvf crawler.jar -C crawler/ .
jar cvf language_utils.jar -C language_utils/ .

jar cvf batch.jar -C batch/ .

jar cvf dictionary.jar -C language_utils/dictionary/ .


