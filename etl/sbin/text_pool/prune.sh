#!/usr/bin/env bash

host=$1

ssh ${host} 'echo && hostname && docker system prune -f'
