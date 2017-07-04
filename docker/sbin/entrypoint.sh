#!/usr/bin/env bash

if [[ "${ROOT_INIT_DIR}" != "" ]] ; then
    echo "사용자 계정 생성 및 root init.d 실행"
    for init_script in $(ls ${ROOT_INIT_DIR}/*.sh) ; do
        echo "${init_script}..."
        ${init_script}
    done
fi

if [[ "${USER_INIT_DIR}" != "" ]] ; then
    echo "사용자 init.d 실행"
    /usr/local/sbin/set_user_permission.sh /usr/local/sbin ${USER_INIT_DIR} ${ROOT_INIT_DIR}

    for init_script in $(ls ${USER_INIT_DIR}/*.sh) ; do
        echo "${init_script}..."
        gosu ${USER} ${init_script}
    done
fi

# 명령어에 따른 실행
if [[ "$@" == "" ]] ; then
    echo "실행 명령이 지정되어 있지 않을 경우: supervisord 데몬 실행"

    /usr/bin/supervisord
elif [[ "${USER}" != "" ]] ; then
    echo "실행 명령이 지정되어 있고 사용자가 지정된 경우: 사용자 계정으로 실행"

    gosu ${USER} "$@"
else
    exec "$@"
fi
