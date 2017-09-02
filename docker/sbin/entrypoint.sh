#!/usr/bin/env bash

if [[ -d "${ROOT_INIT_DIR}" ]] ; then
    echo "사용자 계정 생성 및 root init.d 실행"
    for init_script in $(ls ${ROOT_INIT_DIR}/*.sh) ; do
        echo "${init_script}..."
        ${init_script}
    done
fi

# 명령어에 따른 실행
if [[ "$@" == "" ]] ; then
    echo "실행 명령이 지정되어 있지 않을 경우: supervisord 데몬 실행"

    /usr/bin/supervisord
else
    exec "$@"
fi
