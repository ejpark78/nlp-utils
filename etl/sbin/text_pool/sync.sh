#!/usr/bin/env bash

host=$1
merge_home=$2
merge_path=${merge_home}/${host}

ssh ${host} "sudo chown -R ejpark:ejpark data/*"
ssh ${host} "sudo find data/ -empty -delete"

# 파일 동기화
mkdir -p ${merge_path}
rsync -avz ${host}:data/ ${merge_path}/

