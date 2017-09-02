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
"

host="$1"

script_home=$(dirname "$(readlink -f "$0")")
echo "script_home: ${script_home}, $PWD"

if [ "${host}" != "" ] ; then
    if [[ "${host_name}" != $(hostname) ]] ; then
        rsync -avz ${option} $PWD/ ${host}:/home/docker/crawler/
    fi
else
    for host_name in $(cat ${script_home}/hosts | grep -v ^#) ; do
        if [[ "${host_name}" != $(hostname) ]] ; then
            printf "\n%s\n" ${host_name}
            ssh ${host_name} "rm -rf /home/docker/crawler/.ssh"
            ssh ${host_name} "rm -rf /home/docker/crawler/.pycharm_helpers"
            ssh ${host_name} "rm -rf /home/docker/crawler/dictionary"
            ssh ${host_name} "rm -rf /home/docker/crawler/dictionary.jar"
            ssh ${host_name} "rm -rf /home/docker/crawler/resource"
            ssh ${host_name} "rm -rf /home/docker/crawler/parser"
            ssh ${host_name} "rm -rf /home/docker/crawler/model"
            ssh ${host_name} "rm -rf /home/docker/crawler/etc"
            ssh ${host_name} "rm -rf /home/docker/crawler/__pycache__"
            ssh ${host_name} "rm -rf /home/docker/crawler/wrap"
            ssh ${host_name} "rm -rf /home/docker/crawler/notebook"
            ssh ${host_name} "rm -rf /home/docker/crawler/docker"
            ssh ${host_name} "rm -rf /home/docker/crawler/data"
            ssh ${host_name} "rm -rf /home/docker/crawler/metastore_db"
            ssh ${host_name} "rm -rf /home/docker/crawler/src"
            ssh ${host_name} "rm -rf /home/docker/crawler/.ipynb_checkpoints"
            rsync -avz ${option} $PWD/ ${host_name}:/home/docker/crawler/
        fi
    done
fi
