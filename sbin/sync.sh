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
"

host="$1"

script_home=$(dirname "$(readlink -f "$0")")
echo "script_home: ${script_home}"

if [ "${host}" != "" ] ; then
    push.sh ${host} "${option}"
else
    for host_name in $(cat ${script_home}/hosts | grep -v ^#) ; do
        if [[ "${host_name}" != $(hostname) ]] ; then
            printf "\n%s\n" ${host_name}
            push.sh ${host_name} "${option}"
        fi
    done
fi
