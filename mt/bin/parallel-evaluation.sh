#!/usr/bin/env bash

set -x #echo on

prefix=$1
src=$2
trg=$3
tst=$4

split -d -a 7 -l 5000 ${prefix}.${src} ${prefix}.part. --additional-suffix .${src}
split -d -a 7 -l 5000 ${prefix}.${trg} ${prefix}.part. --additional-suffix .${trg}
split -d -a 7 -l 5000 ${prefix}.${tst} ${prefix}.part. --additional-suffix .${tst}

ls -1 ${prefix}.part.*.${src} \
    | sed 's/\.'${src}'//' \
    | xargs -I{} echo "bin/evaluation.sh {} ${src} ${trg} ${tst}" \
    | parallel -k --ungroup -j$(nproc)

cat ${prefix}.part.*.bleu.json | bzip2 - > ${prefix}.bleu.json.bz2

rm ${prefix}.part.*
