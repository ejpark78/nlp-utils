#!/usr/bin/env bash

set -x #echo on

watch -n 30 -d 'docker stats --no-stream --all --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"'
