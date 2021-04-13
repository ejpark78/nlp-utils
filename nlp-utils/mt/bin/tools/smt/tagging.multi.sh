#!/bin/bash

source "$TOOLS/lib_moses.sh"

#set -o verbose #echo on
lang="$1"
in_file="$2"
column="$3"
out_file="$4"
unit="$5"

max_core="$(nproc)"

if [[ ! -f "$in_file" ]] || [[ "$lang" == "" ]] || [[ "$column" == "" ]] || [[ "$out_file" == "" ]] ; then
    echo "Uage: "$(basename "$0")" [lang: ko, cn, en, fr, es] [in file] [column] [out file] [unit]"
    exit 1
fi

if [[ "$unit" == "" ]] ; then
    unit=24000
fi

if [[ "$lang" == "" ]] ; then
    lang="ko"
fi

echo -e "in_file: '$in_file', lang: '$lang', column: '$column', out_file: '$out_file', unit: '$unit'" 1>&2

# unzip
# org_in_file=""
# if [[ $(file "--mime-type" "$in_file" | cut -d' ' -f2) == "application/gzip" ]] ; then
#     zcat "$in_file" > "$in_file.unzip"
#     sync

#     org_in_file="$in_file"
#     in_file="$in_file.unzip"
# fi

org_ifs="$IFS"

IFS=$'\t' ret=($(gunzip_file "$in_file"))
in_file="${ret[0]}"
org_in_file="${ret[1]}"

IFS="$org_ifs"

echo -e "in_file: '$in_file', org_in_file: '$org_in_file'"

# get length of in file
len=$(wc -l "$in_file" | cut -d' ' -f1)

if (( "$len" > "$unit" )) ; then
    split -d -a 5 -l$unit "$in_file" "$in_file.part."
    sync

    if [[ -f "$out_file" ]] ; then
        rm "$out_file"
        sync
    fi

    # IFS=$' \t\n'
    for fname_in in $(ls -1 "$in_file.part."*) ; do
        ext="${fname_in##*.}"
        echo -e "part ext: $ext" 1>&2

        tagging_file_multi "$lang" "$in_file.part.$ext" "$out_file.part.$ext" $max_core $column
        sync

        cat "$out_file.part.$ext" >> "$out_file"
        sync && rm "$in_file.part.$ext" "$out_file.part.$ext"
    done
else
    tagging_file_multi "$lang" "$in_file" "$out_file" $max_core $column
fi
sync

# delete unzip file
if [[ -f "$org_in_file" ]] ; then
    rm "$in_file"
    sync
fi

