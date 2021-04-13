#!/bin/bash

f=$1
body=$2
header=$3

if [[ "$body" == "" ]]; then
  body=$f.body
fi

if [[ "$header" == "" ]]; then
  header=$f.header
fi

total=`wc -l "$f" |cut -d' ' -f1`

cut=$((total - 1))

echo -e "total: $total"
echo -e "cut: $cut"

cat $f | head -n1 > $header
cat $f | tail -n$cut > $body
