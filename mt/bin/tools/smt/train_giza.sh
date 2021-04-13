#!/bin/bash
#############################################################
# train.sh [src] [trg] [train]
# train.sh ko en train.ko-en
#############################################################
path=$PWD

src=$1
trg=$2
train=$3

max_core=12
#############################################################
path=${path/\/home\/ejpark\/workspace\/model\/${src}-${trg}\//}

echo $src
echo $trg
echo $path
echo $train
#############################################################

echo "# train moses"
perl "$MOSES_SCRIPTS/train-model.perl" \
    -first-step 1 -last-step 2 \
    -write-lexical-counts \
    -external-bin-dir "$MOSES/bin" \
    -parallel -cores $max_core \
    -mgiza -mgiza-cpus $max_core \
    -sort-buffer-size 60G -sort-batch-size 253 \
    -sort-compress gzip -sort-parallel $max_core \
    -root-dir $PWD \
    -model-dir $PWD \
    -corpus "$PWD/$train" \
    -f $src -e $trg \
    -alignment grow-diag-final-and \
    -reordering msd-bidirectional-fe \
    -lm "0:5:$WORKSPACE/model/lm/$trg.lm_binary:8" \
    2>&1 | tee train-model.log
sync
#############################################################


#############################################################

echo DONE
