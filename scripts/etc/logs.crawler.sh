#!/bin/bash

image="crawler:cluster"

for host_name in gollum gollum01 gollum02 gollum03 ; do
    echo -e "\n${host_name}"
    for container_name in crawler-job-1 crawler-job-2 crawler-job-3 crawler-job-4 ; do
        echo -e "\n${container_name}"
        docker -H ${host_name}:2375 logs --tail 10 ${container_name}
    done
done
