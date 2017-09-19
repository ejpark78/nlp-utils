#!/usr/bin/env bash

option="
 --delete
 --exclude=.git
 --exclude=.idea
 --exclude=__pycache__
 --exclude=data
 --exclude=docker
 --exclude=example
 --exclude=log
 --exclude=metastore_db
 --exclude=src
 --exclude=tmp
 --exclude=wrap
 --exclude=section
 --exclude=dictionary.jar
 --exclude=.pycharm_helpers
 --exclude=.ssh
 --exclude=dictionary
 --exclude=resource
 --exclude=parser
 --exclude=model
 --exclude=etc
 --exclude=notebook
 --exclude=.ipynb_checkpoints
 --exclude=*.jar
"

host="$1"
dst_path="/data/nlp_home/docker/crawler"

script_home=$(dirname "$(readlink -f "$0")")
echo "script_home: ${script_home}, $PWD"

if [ "${host}" != "" ] ; then
    if [[ "${host_name}" != $(hostname) ]] ; then
        rsync -avz ${option} $PWD/ ${host}:${dst_path}/
    fi
else
    for host_name in $(cat ${script_home}/hosts | grep -v ^#) ; do
        if [[ "${host_name}" == $(hostname) ]] ; then
            continue
        fi

        printf "\n%s\n" ${host_name}
#        ssh ${host_name} "sudo mkdir -p ${dst_path}"
#        ssh ${host_name} "sudo chown -R ejpark:ejpark ${dst_path}"
#        ssh ${host_name} "rm -rf ${dst_path}/.ssh"
#        ssh ${host_name} "rm -rf ${dst_path}/.pycharm_helpers"
#        ssh ${host_name} "rm -rf ${dst_path}/dictionary"
#        ssh ${host_name} "rm -rf ${dst_path}/dictionary.jar"
#        ssh ${host_name} "rm -rf ${dst_path}/resource"
#        ssh ${host_name} "rm -rf ${dst_path}/parser"
#        ssh ${host_name} "rm -rf ${dst_path}/model"
#        ssh ${host_name} "rm -rf ${dst_path}/etc"
#        ssh ${host_name} "rm -rf ${dst_path}/__pycache__"
#        ssh ${host_name} "rm -rf ${dst_path}/wrap"
#        ssh ${host_name} "rm -rf ${dst_path}/notebook"
#        ssh ${host_name} "rm -rf ${dst_path}/docker"
#        ssh ${host_name} "rm -rf ${dst_path}/data"
#        ssh ${host_name} "rm -rf ${dst_path}/metastore_db"
#        ssh ${host_name} "rm -rf ${dst_path}/src"
#        ssh ${host_name} "rm -rf ${dst_path}/.ipynb_checkpoints"
        rsync -avz ${option} $PWD/ ${host_name}:${dst_path}/
    done
fi
