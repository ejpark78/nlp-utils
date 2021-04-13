#!/bin/bash

train_log="$1"
fname_out="$2"

if [[ ! -d "$train_log" ]] || [[ "$fname_out" == "" ]] ; then
    echo "Uage: "$(basename $0)" [train log path] [out file name]"
    exit 1
fi

# if [[ "$train_log" == "" ]] ; then
#     train_log="train-log"
# fi

# if [[ "$fname_out" == "" ]] ; then
#     fname_out="$train_log/A3.final.gz"
# fi

echo -e "train log dir: '$train_log', fname out: '$fname_out'" 1>&2

final_list=()
for f_final in $(ls "$train_log/"*.A3.final.gz) ; do
    fname=${f_final%.*}

    zcat "$f_final" \
        | grep "^# Sentence pair" | cut -d':' -f 2 | tr -d ' ' \
        | gzip - > "$fname.tmp.gz"
    
    final_list+=("$fname.tmp.gz")
done
sync

merge_file.pl $(printf "\"%s\" " "${final_list[@]}") \
    | gzip - > "$fname_out"
sync

rm $(printf "%s " "${final_list[@]}")
sync
