#!/usr/bin/env bash

ls -1 data/batch/*.json.bz2 | sort -r > data/batch/list.txt

parallel -j 8 -k --bar -a data/batch/list.txt "./sbin/batch.sh {}"
