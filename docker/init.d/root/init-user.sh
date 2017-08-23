#!/usr/bin/env bash

exit 1

# 사용자 계정 생성
if [[ "${USER}" == "" ]] ; then
    exit 1
fi

# default UID
if [[ "${UID}" == "" ]] ; then
    export UID=1000
fi

# default GID
if [[ "${GID}" == "" ]] ; then
    export GID=${UID}
fi

echo "사용자 계정 생성: USER: ${USER}, UID: ${UID}, GID: ${GID}"
export HOME=/home/${USER}

echo "사용자 계정 및 그룹 생성"
addgroup --gid ${GID} ${USER}
adduser --disabled-password --gecos '' --shell /bin/bash --uid ${UID} --gid ${GID} ${USER}
adduser ${USER} sudo

chown ${UID}:${GID} ${HOME}

echo "사용자 암호 설정"
if [[ "${PASSWD}" != "" ]] ; then
    echo "${USER}:${PASSWD}" | chpasswd
fi

echo "계정 설정 복사"
if [ -f "/root/bashrc" ] ; then
    cat /root/bashrc >> ${HOME}/.bashrc
    chown ${UID}:${GID} ${HOME}/.bashrc
fi

for fname in .tmux.conf .vimrc ; do
    if [ -f "/root/${fname}" ] ; then
        cp "/root/${fname}" ${HOME}/
        chown ${UID}:${GID} ${HOME}/${fname}
    fi
done

for dname in .ssh .jupyter ; do
    if [ -d "/root/${dname}" ] ; then
        cp -r /root/${dname} ${HOME}/
        chown -R ${UID}:${GID} ${HOME}/${dname}
    fi
done

if [ ! -f "${HOME}/.hushlogin" ] ; then
    touch ${HOME}/.hushlogin
    chown ${UID}:${GID} ${HOME}/.hushlogin
fi

echo "sudoer 사용자 권한 추가"
echo "%sudo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

