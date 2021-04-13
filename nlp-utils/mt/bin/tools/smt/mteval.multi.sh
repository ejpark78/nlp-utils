#!/bin/bash

source "$TOOLS/lib_moses.sh"

max_core=12

tst="$1"
src="$2"
ref="$3"

out="$4"
unit="$5"

if [[ ! -f "$src" ]] || [[ ! -f "$tst" ]] || [[ ! -f "$ref" ]] ; then
    echo "Usage: "$(basename "$0")" tst src ref [out: tst.bleu] [unit: 24000]"
    exit 0
fi

if [ "$out" == "" ] ; then
    out="$tst.bleu"
fi

if [ "$unit" == "" ] ; then
    unit=24000
fi

echo -e "tst: '$tst', src: '$src', ref: '$ref', out: '$out', unit: '$unit'" 1>&2

time {
    if [[ -f "$out" ]] ; then
        rm "$out"
        sync
    fi

    len=$(wc -l "$src" | cut -d' ' -f1)
    if (( "$len" > "$unit" )) ; then
        # split 2,000

        split -d -a 5 -l$unit "$src" "$src.part."
        split -d -a 5 -l$unit "$ref" "$ref.part."
        split -d -a 5 -l$unit "$tst" "$tst.part."
        sync

        for f in $(ls "$src.part."*) ; do
            ext="${f##*.}"
            echo -e "ext: $ext"

            split_mteval "$tst.part.$ext" "$src.part.$ext" "$ref.part.$ext" "$ref.part.bleu" $max_core

            sync && cat "$tst.part.$ext.bleu" >> "$out"
            sync && rm "$tst.part.$ext.bleu" "$tst.part.$ext" "$src.part.$ext" "$ref.part.$ext"
        done
    else
        split_mteval "$tst" "$src" "$ref" "$out" "$ref.part.bleu" $max_core
    fi

    sync
}


