#!/bin/bash

cmd="$1"

# 입력 파라메터 확인
if [ "${cmd}" == "" ] ; then
    echo "Usage: "$(basename $0)" [command: ex) up down]"
    exit 1
fi

host_name=$(hostname)
yml=docker-compose.yml
header=crawler

case ${cmd} in
    *)
        docker-compose \
            --host ${host_name}:2376 \
            --project-directory ${header} \
            --file ${yml} \
            $@
        ;;
esac