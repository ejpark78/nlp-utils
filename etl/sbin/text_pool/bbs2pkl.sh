#!/usr/bin/env bash

bin=$1
filename=$2
result_filename=$3
board_list=$4

python3 ${bin}/lineagem_utils.py \
    -bbs2text \
    -board_list ${board_list} \
    -filename ${filename} \
    -result_filename ${result_filename}
