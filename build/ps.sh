#!/usr/bin/env bash

host=$1

ssh ${host} 'hostname && docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}" && echo'
