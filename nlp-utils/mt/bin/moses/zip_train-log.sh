#!/bin/bash

model_dir="$1"

if [[ "$model_dir" == "" ]] ; then
    model_dir="$PWD"  
fi

train_log="$model_dir/train-log"
if [[ ! -d "$train_log" ]] ; then
    mkdir -p "$train_log"
    sync
fi

mv "$model_dir/"giza.*-*/*.A3.final.gz "$train_log/"
mv "$model_dir/"lex.* "$train_log/"

mv "$model_dir/moses.ini" "$train_log/"
mv "$model_dir/phrase-table.gz" "$model_dir/reordering-table.wbe-msd-bidirectional-fe.gz" "$train_log/"

sync

rm -rf "$model_dir/corpus/"
rm -rf "$model_dir/"giza.*-*
rm "$model_dir/aligned.grow-diag-final-and"
rm "$model_dir/"extract.* 
rm "$model_dir/"*.log

bzip2 "$train_log/"*
sync
