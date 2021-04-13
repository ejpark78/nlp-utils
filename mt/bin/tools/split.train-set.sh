#!/bin/bash

# split.train-set.sh input.gz 10000 100000

filename="$1"
test_size="$2"
dev_size="$3"

# check arguments
if [[ "$filename" == "" ]] || [[ "$test_size" == "" ]] ; then
  echo "Uage: "$(basename "$0")" <input file> <test set size> <dev set size>"
  exit 1
fi

ext=${filename##*.}
fname=$(basename $filename .$ext)

total=$(zcat "$filename" | wc -l | cut -d' ' -f1)

# 1. shuf
zcat "$filename" | shuf | gzip - > "$fname.shuf.gz"
filename_shuf="$fname.shuf.gz"

# 2. split test set
zcat "$filename_shuf" | head -n $test_size | gzip - > "$fname.test-set.gz"

# 3. split dev set
start_train=$((test_size + 1))
if [[ "$dev_size" != "" ]] ; then
    zcat "$filename_shuf" | tail -n +$((test_size+1)) | head -n $dev_size | gzip - > "$fname.dev-set.gz"
    start_train=$((test_size + dev_size + 1))
fi

# 4. split train set
zcat "$filename_shuf" | tail -n +$start_train | gzip - > "$fname.train-set.gz"

echo "train-set: " $(zcat "$fname.train-set.gz" | wc -l)
echo "test-set: " $(zcat "$fname.test-set.gz" | wc -l)

if [[ -e "$fname.dev-set.gz" ]] ; then
    echo "dev-set: " $(zcat "$fname.dev-set.gz" | wc -l)
fi
