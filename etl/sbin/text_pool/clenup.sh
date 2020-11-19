#!/usr/bin/env bash

host=$1
data_dir=$2

# 결과 삭제
ssh ${host} "sudo rm -rf ${data_dir}/*"
ssh ${host} "docker system prune -f"
