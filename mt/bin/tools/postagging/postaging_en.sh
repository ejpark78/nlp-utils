#!/bin/bash

function postagging_english {
   local f=$1
   local out=$2

   cat $f | perl -nle 's/\|/ /g; s/\s+/ /g; print' \
      | python `which postag_en.py` \
      > $out
}

function postagging {
   local f=$1
   local out=$2

   split.sent.sh $f 12 $f.

   local buf=""
   local buf_pos=""
   for i in {0..11}
   do
      c=$(printf '%02d' $i)

      f_in=$f.$c

      buf="$buf $f_in"
      buf_pos="$buf_pos $f_in.pos"

      postagging_english $f_in $f_in.pos &
   done

   wait

   sync

   cat $buf_pos > $out
   sync

   rm $buf $buf_pos
}

## main
if [ "$1" == "" ] ; then
    echo "Usage: `basename $0` engilsh.txt"
    exit 0
fi

f=$1
out=$2

if [ "$out" == "" ] ; then
    out=$f.pos
fi

echo -e "f: $f, out: $out"

postagging $f $out
sync
#############################################################

