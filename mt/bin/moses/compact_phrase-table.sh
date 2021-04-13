#!/bin/bash

model_dir="$1"

if [[ "$model_dir" == "" ]] ; then
    model_dir="$PWD"  
fi

"$MOSES/bin/processPhraseTableMin" \
    -nscores 4 -threads 12 \
    -in "$model_dir/phrase-table.reduced.gz" \
    -out "$model_dir/phrase-table.reduced" \
    2>&1 | tee "$model_dir/build-binary-model.log"
sync

"$MOSES/bin/processLexicalTableMin" \
    -threads 12 \
    -in "$model_dir/reordering-table.wbe-msd-bidirectional-fe.reduced.gz" \
    -out "$model_dir/reordering-table.reduced" \
    2>&1 | tee -a "$model_dir/build-binary-model.log"
sync

# change ini
cat "$model_dir/moses.ini" \
    | sed 's/PhraseDictionaryMemory/PhraseDictionaryCompact/' \
    | sed 's/phrase-table.gz/phrase-table.reduced/' \
    | sed 's/reordering-table.wbe-msd-bidirectional-fe.gz/reordering-table.reduced/' \
    > "$model_dir/moses.binary.ini"
sync

