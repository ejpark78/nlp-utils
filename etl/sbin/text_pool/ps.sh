#!/usr/bin/env bash

host=$1

ssh ${host} 'echo && hostname && docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"'
