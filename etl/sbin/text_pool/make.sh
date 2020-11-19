#!/usr/bin/env bash

home=$1
host=$2
tag=$3

ssh ${host} "echo && hostname && cd ${home}/ && make ${tag}"
