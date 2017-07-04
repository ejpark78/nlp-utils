#!/usr/bin/env bash

image="crawler:dev"
name="crawler_dev_"$(hostname)

docker stop ${name}
docker rm ${name}

PASSWD="nlplab"

options="
 --name ${name}
 --hostname ${name}

 --restart always

 --env USER=$(id -un)
 --env PASSWD=${PASSWD}
 --env UID=$(id -u)
 --env GID=$(id -g)

 --workdir /workspace

 --network gollum-net

 --volume /etc/localtime:/etc/localtime:ro
 --volume /home/ejpark/workspace:/home/ejpark/workspace

--publish 9022:22
"

echo "options: ${options}"
if [[ "$1" == "-it" ]] ; then
    docker run -it --rm ${options} ${image} "$@"
else
    docker run --detach -it --restart always ${options} ${image}
fi
