#!/usr/bin/env bash

cd /usr/local/app

./batch.1.sh &

sleep 10
./batch.2.sh &

sleep 10
./batch.3.sh &

wait
