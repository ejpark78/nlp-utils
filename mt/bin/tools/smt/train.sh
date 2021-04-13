#!/bin/bash

src="$1"
trg="$2"
train="$3"
lm_type="$4"
model_dir="$5"

max_core=12

if [ "$src" == "" ] || [ "$trg" == "" ] || [ "$train" == "" ] ; then
    echo "Uage: "$(basename $0)" [src] [trg] [train] [lm type: local or '']"
    exit 1
fi

if [[ "$model_dir" == "" ]] ; then
    model_dir="$PWD"  
fi

if [[ ! -d "$model_dir/train-log" ]] ; then
    mkdir -p "$model_dir/train-log"
fi

time {
    echo -e "model dir: '$model_dir', src: '$src', trg: '$trg', train: '$train', lm_type: '$lm_type', max_core: '$max_core'" 1>&2
    
    if [[ ! -f "$model_dir/train-log/$train.gz" ]] ; then
        merge_file.pl "$model_dir/$train.$src" "$model_dir/$train.$trg" \
            | gzip - > "$model_dir/train-log/$train.gz"
    fi
    
    lm="$WORKSPACE/model/lm/$trg.lm_binary"
    if [ "$lm_type" == "local" ] ; then
        lmplz -o 5 -S 80% -T /tmp < "$model_dir/$train.$trg" > "$model_dir/train-log/$trg.lm" && sync
        sync && build_binary "$model_dir/train-log/$trg.lm" "$model_dir/$trg.lm_binary"
        
        lm="$model_dir/$trg.lm_binary"
    fi
    sync
    
    echo "# train moses"
    perl "$MOSES_SCRIPTS/train-model.perl" \
        -first-step 1 -last-step 9 \
        -write-lexical-counts \
        -external-bin-dir "$MOSES/bin" \
        -parallel -cores $max_core \
        -mgiza -mgiza-cpus $max_core \
        -sort-buffer-size 60G -sort-batch-size 253 \
        -sort-compress gzip -sort-parallel $max_core \
        -root-dir "$model_dir" \
        -model-dir "$model_dir" \
        -corpus "$model_dir/$train" \
        -f $src -e $trg \
        -alignment grow-diag-final-and \
        -reordering msd-bidirectional-fe \
        -lm "0:5:$lm:8" \
        |& tee "$model_dir/train-log/train-model.log"
    
    sync && filter_phrase-table.sh "$model_dir"
    sync && compact_phrase-table.sh "$model_dir"
    sync && zip_train-log.sh "$model_dir"
    
    sync
}

