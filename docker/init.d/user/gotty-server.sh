#!/usr/bin/env bash

if [[ "${USE_GOTTY}" == 1 ]] ; then
    if [[ "${USE_SSL}" == 1 ]] ; then
        /usr/local/sbin/gotty-server-ssl.sh &
    else
        /usr/local/sbin/gotty-server.sh &
    fi
fi
