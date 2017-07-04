#!/usr/bin/env bash

docker build --network docker_gwbridge --file Dockerfile --tag crawler:dev $PWD
