#!/bin/bash






#split -d -l 211732 training training.

#
#for fname in $(\ls language_utils/data/UCorpus-HG/training.??.bz2 | perl -ple 's/.bz2//') ; do
#    echo ${fname}
#    bzcat ${fname}.bz2 | batch.py | bzip2 - > ${fname}.json.bz2 &
#done
#wait


#fname="language_utils/data/UCorpus-HG/test"
#echo ${fname}
#bzcat ${fname}.bz2 | batch.py | bzip2 - > ${fname}.json.bz2



# 개체명 인식 코퍼스 형식 변환
data_path="language_utils/data/named_entity"
#fname="general.L1.train"
#
#bzcat ${data_path}/${fname}.bz2 \
#    | ./batch.py \
#    | bzip2 - > ${data_path}/${fname}.json.bz2


#
#for fname in baseball.L1.test.train.bz2 baseball.L1.train.bz2 baseball.L2.test.train.bz2 baseball.L2.train.bz2 general.L1.test.train.bz2 general.L1.train.bz2 ner.eval.L1.train.bz2 ner.eval.L2.train.bz2 ; do
#    fname=$(echo ${fname} | perl -ple 's/\.bz2//')
#    echo ${fname}
#
#    bzcat ${data_path}/${fname}.bz2 \
#        | ./batch.py \
#        | bzip2 - > ${data_path}/${fname}.json.bz2
#
#done
#
#
