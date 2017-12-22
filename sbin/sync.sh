#!/usr/bin/env bash

option="
 --delete
 --exclude=.git
 --exclude=.idea
 --exclude=.ipynb_checkpoints
 --exclude=.pycharm_helpers
 --exclude=.ssh
 --exclude=__pycache__
 --exclude=data
 --exclude=docker
 --exclude=example
 --exclude=log
 --exclude=metastore_db
 --exclude=tmp
 --exclude=wrap
 --exclude=*.jar
 --exclude=resource
 --exclude=parser
 --exclude=model
 --exclude=notebook
"

host="$1"
dst_path="/data/nlp_home/docker/crawler"

script_home=$(dirname "$(readlink -f "$0")")
echo "script_home: ${script_home}, $PWD"

if [ "${host}" != "" ] ; then
    if [[ "${host_name}" != $(hostname) ]] ; then
        rsync -avz -K ${option} $PWD/ ${host}:${dst_path}/
    fi
else
    for host_name in $(cat ${script_home}/hosts | grep -v ^#) ; do
        if [[ "${host_name}" == $(hostname) ]] ; then
            continue
        fi

        printf "\n%s\n%s\n" ${host_name} ${dst_path}
        ssh ${host_name} "sudo mkdir -p ${dst_path}"
        ssh ${host_name} "sudo chown -R ejpark:ejpark ${dst_path}"

#        ssh ${host_name} "rm -rf ${dst_path}/.ssh"

        rsync -avz -K ${option} $PWD/ ${host_name}:${dst_path}/
    done
fi
