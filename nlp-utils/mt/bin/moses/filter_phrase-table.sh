#!/bin/bash

model_dir="$1"

if [[ "$model_dir" == "" ]] ; then
    model_dir="$PWD"  
fi

zcat "$model_dir/phrase-table.gz" \
  | "$MOSES_SCRIPTS/threshold-filter.perl" 0:0.0001,2:0.0001 \
  | gzip - > "$model_dir/phrase-table.reduced.gz" \
  2> "$model_dir/reduce-model.log"
sync

zcat "$model_dir/reordering-table.wbe-msd-bidirectional-fe.gz" \
  | perl "$MOSES_SCRIPTS/remove-orphan-phrase-pairs-from-reordering-table.perl" \
    "$model_dir/phrase-table.reduced.gz" \
  | gzip - > "$model_dir/reordering-table.wbe-msd-bidirectional-fe.reduced.gz" \
  2> "$model_dir/reduce-model.log"
sync

# change ini
cat "$model_dir/moses.ini" \
  | sed 's/phrase-table.gz/phrase-table.reduced.gz/' \
  | sed 's/reordering-table.wbe-msd-bidirectional-fe.gz/reordering-table.wbe-msd-bidirectional-fe.reduced.gz/' \
  > "$model_dir/moses.reduced.ini"
sync

