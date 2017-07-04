#!/bin/bash

name="hadoop_"$(hostname)

image="hadoop:dev"

workspace="/home/ejpark/workspace"

docker stop ${name}
docker rm ${name}

options="
    --name ${name}
    --hostname ${name}

    --workdir /workspace
    --network gollum-net

    --volume /etc/localtime:/etc/localtime:ro
    --volume ${workspace}:/workspace
"

command="/bin/bash"

echo "options: ${options}, ${command}"
#docker run -it --rm ${options} ${image} ${command}
docker run --detach -it --restart always ${options} ${image} ${command}
#docker logs -f ${name}
