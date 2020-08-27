#!/usr/bin/env bash

# 형태소 분석: single file
#time bzcat dictionary/crawler-naver-dictionary-bitext.json.bz2 \
#    | PYTHONPATH=.. python3 pre_process.py --colum korean,english \
#    | bzip2 - > dictionary/crawler-naver-dictionary-bitext.morp.json.bz2

filename=$1

# 형태소 분석: multi-file
bzcat ${filename} \
    | split -d -a 4 -l 10000 - ${filename}.part.

ls -1 ${filename}.part.???? \
    | xargs -I{} echo "cat {} | PYTHONPATH=.. python3 pre_process.py --colum korean,english > {}.out" \
    | parallel -j8 --ungroup -k

cat ${filename}.part.????.out \
    | bzip2 - > ${filename}.morp.bz2

rm ${filename}.part.???? ${filename}.part.????.out
sync

rename 's/\.json\.bz2\.morp/.morp.json/' ${filename}.morp.bz2
