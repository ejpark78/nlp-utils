#!/bin/bash

model_dir="$1"

if [[ "$model_dir" == "" ]] ; then
    model_dir="$PWD"  
fi

if [[ -f "$model_dir/moses.reduced.ini" ]] ; then
    cat "$model_dir/moses.reduced.ini" | sed 's/\.lm_binary/.lm/' > "$model_dir/moses.reduced.lm.ini"
fi

if [[ -f "$model_dir/moses.binary.ini" ]] ; then
    cat "$model_dir/moses.binary.ini" | sed 's/\.lm_binary/.lm/' > "$model_dir/moses.binary.lm.ini"
fi
