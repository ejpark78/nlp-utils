#!/usr/bin/env bash

host=$1

ssh ${host} 'echo && hostname && docker images'
