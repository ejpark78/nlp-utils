#!/usr/bin/env bash

in=$1
out=$2

mkdir -p ${out}

rm ${out}/*
pbzip2 -d -c ${in} > ${out}/data.json
sync

split -a 4 -d -l100000 ${out}/data.json ${out}/p.
sync

pbzip2 ${out}/p.*
sync

rm ${out}/data.json
ls -1 ${out}/p.*.bz2 > ${out}/file.list
