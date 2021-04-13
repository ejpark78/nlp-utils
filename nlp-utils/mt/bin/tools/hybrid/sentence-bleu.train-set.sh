#!/bin/bash

train_log="$1"

if [[ "$train_log" == "" ]] ; then
    echo "Uage: "$(basename "$0")" [train log dir]"
    exit 1
fi

# extract ibm score
extract_ibm-score.sh "$train_log" "$train_log/A3.final.gz"

# get sentence bleu
src="$train_log/train.ko"
ref="$train_log/train.en"
tst="$src.out"

zcat "$src.gz" > "$src"
zcat "$ref.gz" > "$ref"

sync && moses -threads 12 -f "$train_log/../moses.binary.ini" < "$src" > "$tst"
sync && mteval.multi.sh "$tst" "$src" "$ref" "$tst.bleu" 24000

# merge A3.final, sentence bleu, tst, src, trg
wc -l "$tst.bleu" "$tst" "$src" "$ref"

merge_file.pl "$train_log/A3.final.gz" "$tst.bleu" "$tst" "$src.gz" "$ref.gz"
sync

rm "$src" "$ref"
