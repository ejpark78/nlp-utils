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
mv "$model_dir/"train.* "$train_log/"

mv "$model_dir/moses.ini" "$train_log/"
mv "$model_dir/phrase-table.gz" "$model_dir/reordering-table.wbe-msd-bidirectional-fe.gz" "$train_log/"

# mv "$model_dir/moses.reduced.ini" "$train_log/"
# mv "$model_dir/phrase-table.reduced.gz" "$model_dir/reordering-table.wbe-msd-bidirectional-fe.reduced.gz" "$train_log/"

# if [[ -f "en.lm" ]] ; then
#     mv "$model_dir/en.lm" "$train_log/"
# fi

sync

rm -rf "$model_dir/corpus/"
rm -rf "$model_dir/"giza.*-*
rm "$model_dir/aligned.grow-diag-final-and"
rm "$model_dir/"extract.* 
rm "$model_dir/"*.ko "$model_dir/"*.en "$model_dir/"*.es "$model_dir/"*.fr
rm "$model_dir/"*.log

gzip "$train_log/"* 
sync
