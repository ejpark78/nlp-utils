#!/usr/bin/env bash

#set -x #echo on

prefix=$1
src=$2
trg=$3
tst=$4

# 자동 평가
bin/wrap.pl -type src -in "${prefix}.${src}" -out "${prefix}.src.scr"
bin/wrap.pl -type ref -in "${prefix}.${trg}" -out "${prefix}.ref.scr"
bin/wrap.pl -type tst -in "${prefix}.${tst}" -out "${prefix}.tst.scr"
sync

bin/mteval-v14c.pl -d 2 \
    -s "${prefix}.src.scr" \
    -r "${prefix}.ref.scr" \
    -t "${prefix}.tst.scr" \
    > "${prefix}.bleu"
sync

~/bin/merge_eval.py \
   -bleu "${prefix}.bleu" \
   -src "${prefix}.${src}" \
   -tgt "${prefix}.${trg}" \
   -tst "${prefix}.${tst}" \
   > "${prefix}.bleu.json"
sync
