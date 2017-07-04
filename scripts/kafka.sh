#!/usr/bin/env bash

kafka-topics.sh --create --zookeeper master:2181 --replication-factor 1 --partitions 1 --topic crawler


kafka-console-producer.sh --broker-list master:9092 --topic crawler



kafka-topics.sh --list --zookeeper master:2181


kafka-console-consumer.sh --bootstrap-server master:9092 --topic crawler --from-beginning
kafka-console-consumer.sh --bootstrap-server master:9092 --topic crawler

kafka-topics.sh --describe --zookeeper master:2181 --topic crawler


kafka-topics.sh --delete --zookeeper master:2181 --topic crawler



zkCli.sh  -server master:2181 rmr /brokers/topics/crawler
zkCli.sh  -server master:2181 rmr /admin/delete_topics/crawler

zookeeper-shell.sh master:2181 rmr /brokers/topics/crawler
zookeeper-shell.sh master:2181 rmr /admin/delete_topics/crawler

