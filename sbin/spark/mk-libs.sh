#!/usr/bin/env bash

jar cv0f spark-libs.jar -C $SPARK_HOME/jars/ .

hdfs dfs -mkdir -p /libs/
hdfs dfs -put spark-libs.jar /libs/


$ cat /usr/local/spark/conf/spark-defaults.conf 

spark.yarn.archive hdfs://master:9000/libs/spark-libs.jar

