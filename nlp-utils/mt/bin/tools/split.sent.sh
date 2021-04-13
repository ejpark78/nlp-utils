#!/bin/bash

# MAKE NEW WORKSPACE
# Made by EJ. Park 

# PRINT USAGE
usage="\
Usage: $0 [FILE_NAME] [PART_COUNT] [PREFIX]
       $0 corpus/btec/word/all/data-set/train.kr 2 btec.all.
"

# if [[ $# < 3 ]] ; then
#     echo  "$usage" 1>&2
#     exit 0
# fi

FILE="$1"
PART="$2"
PREFIX="$3"

total=$(wc -l "$FILE" | cut -d' ' -f1)
cnt=$((total/PART + 1))

echo "# FILE:$FILE, PART:$PART, PREFIX:$PREFIX, total:$total, cnt:$cnt" 1>&2

split -d -a 2 -l$cnt "$FILE" "$PREFIX"

# split -d -a 2 -l`wc -l "$FILE" | awk -F' ' '{printf \"%d\", $1/'$PART'+1;}'` "$FILE" "$PREFIX"
