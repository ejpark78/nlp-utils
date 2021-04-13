#!/usr/bin/env bash

# sudo usermod -aG docker ejpark

cmd="$1"
image="$2"
tag="$3"
version="$4"


if [[ "$cmd" == "rm" ]] ; then
    docker rm $(docker ps -q -f status=exited)
    docker ps -a
    exit 1
fi

if [[ "$cmd" == "clean" ]] ; then
    docker rmi $(docker images | grep "^<none>" | awk "{print $3}")
    docker rmi $(docker images -f "dangling=true" -q)
    
    docker run \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /var/lib/docker:/var/lib/docker \
        --rm martin/docker-cleanup-volumes

    docker images
    exit 1
fi

if [[ "$cmd" == "ps" ]] ; then
    docker ps -a
    exit 1
fi

# check arguments
if [[ "$cmd" == "" ]] || [[ "$image" == "" ]] ; then
    echo "Uage: "$(basename "$0")" <command: build, run, clean, rm> <image name> <tag> <version>"
    exit 1
fi

if [[ "$tag" == "" ]] ; then
    tag="$image"
fi

if [[ "$version" == "" ]] ; then
    version="latest"
fi

# command
if [[ "$cmd" == "run" ]] || [[ "$cmd" == "start" ]] ; then
    if [[ "$image" == "tensorflow" ]] ; then
        docker run \
            -it --user ejpark \
            --rm -p 9988:8888 \
            --hostname "$tag" \
            --volume /etc/localtime:/etc/localtime:ro \
            --volume /home/ejpark/workspace:/workspace \
            --volume /home/ejpark/workspace/tools:/tools \
            --name "$tag" \
            "$image"
    fi

    if [[ "$image" == "workspace" ]] ; then
        docker run \
            -it --user ejpark \
            --rm -p 8888:8888 \
            --hostname "$tag" \
            --volume /etc/localtime:/etc/localtime:ro \
            --volume /home/ejpark/workspace:/workspace \
            --volume /home/ejpark/workspace/tools:/tools \
            --name "$tag" \
            "$image"
    fi

    if [[ "$image" == "transmission" ]] ; then
        docker run --detach \
            --publish 8091:9091 \
            --restart always \
            --name "$tag" \
            --volume /etc/localtime:/etc/localtime:ro \
            --volume /home/ejpark/md0/plex/downloads:/var/lib/transmission-daemon/downloads \
            --volume /home/ejpark/md0/plex/incomplete:/var/lib/transmission-daemon/incomplete \
            "$image"
    fi

    if [[ "$image" == "plex" ]] ; then
        docker run --detach \
            --net=host \
            --publish 32400:32400 \
            --restart always \
            --name "$tag" \
            --volume /etc/localtime:/etc/localtime:ro \
            --volume /home/ejpark/md0/plex:/media \
            --volume /home/ejpark/md0/plex/config:/config \
            "$image"
    fi

    if [[ "$image" == "nginx" ]] ; then
        docker run --detach \
            --name "$tag" \
            --volume /etc/localtime:/etc/localtime:ro \
            --volume /home/ejpark/md0/www/html:/usr/share/nginx/html \
            --publish 80:80 \
            "$image"
    fi

    if [[ "$image" == "flask" ]] ; then
        docker run --detach \
            --publish 8081:8081 \
            --user ejpark \
            --restart always \
            --name "$tag" \
            --volume /etc/localtime:/etc/localtime:ro \
            --volume /home/ejpark/md0/www/books:/app \
            --volume /home/ejpark/md0/books:/books \
            "$image"
    fi
fi

if [[ "$cmd" == "debug" ]] ; then
    if [[ "$image" == "flask" ]] ; then
        debug
        docker run \
            -a stdin -a stdout -a stderr \
            --user ejpark \
            --publish 8081:8081 \
            --name "$tag" \
            --volume /etc/localtime:/etc/localtime:ro \
            --volume /home/ejpark/md0/www/books:/app \
            --volume /home/ejpark/md0/books:/books \
            "$image"
    fi
fi

if [[ "$cmd" == "stop" ]] ; then
    docker stop "$tag"
    docker rm -f "$tag"
    docker ps -a
    docker images
fi

if [[ "$cmd" == "build" ]] ; then
    docker build --rm --no-cache --tag "$image" "."
    # docker build --rm --tag "$image" "."
    docker images
fi

if [[ "$cmd" == "save" ]] ; then
    docker images
    docker save "$image:$version" | gzip - > "$image.tar.gz"
    chown ejpark:ejpark "$image.tar.gz"
fi

if [[ "$cmd" == "load" ]] ; then
    docker load < "$image.tar.gz"
    docker images
fi
