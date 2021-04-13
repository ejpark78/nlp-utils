#!/bin/bash
#############################################################
# functions
#############################################################
function postagging_korean {
   local f=$1
   local out=$2

   cat $f \
      | tagging_ko ~/workspace/model/tagger/ko/model.syllpostagger.ap.crfsuite \
      > $out
}
#############################################################
function tokenize_korean {
   local f=$1	
   local out=$2

   cat $f \
      | tagging_ko ~/workspace/model/tagger/ko/model.syllpostagger.ap.crfsuite \
      | remove_pos_tag.pl > $out
}
#############################################################
function tokenize_western {
   local f=$1  
   local l=$2
   local out=$3

   cat $f | tokenizer.perl -l $l | convert_code.pl > $out
}
#############################################################
function tokenize_bitext {
   local f=$1
   local l=$2

   split.sent.sh $f.$l 12 $f.$l.

   local buf=""
   local buf_tok=""
   for i in {0..11}
   do
      c=$(printf '%02d' $i)

      f_in=$f.$l.$c
      buf="$buf $f_in"
      buf_tok="$buf_tok $f_in.tok"

      if [ "$l" == "ko" ]; then
         tokenize_korean $f_in $f_in.tok &
      fi

      if [ "$l" != "ko" ]; then
         tokenize_western $f_in $l $f_in.tok &
      fi
   done

   wait

   sync

   cat $buf_tok > $f.tok.$l 
   sync

   rm $buf $buf_tok $f.$l 
}
#############################################################
function tokenize_src_refs() {
  local f=$1
  local l1=$2
  local l2=$3
  f_list=$4
  ref_cnt=$5

  # split src & ref
  cut_eval_set.pl -f $f
  sync

  mv $f.src $f.$l1
  sync

  # tokenize src & ref
  tokenize_bitext $f $l1

  f_list="$f.tok.$l1"

  local buf_ref=

  rm $f.refs
  sync
  
  for ref in $(ls $f.ref?)
  do
    mv $ref $ref.$l2
    sync

    tokenize_bitext $ref $l2

    f_list="$f_list $ref.tok.$l2"

    buf_ref="$buf_ref $ref.tok.$l2"

    ref_cnt=$((ref_cnt+1))
  done

  merge_file.pl $buf_ref > $f.refs
}
#############################################################
# main
#############################################################
l1=$1
l2=$2
f=$3

f=${f/\.gz/}

echo $f

f_list=""
ref_cnt=0

zcat $f.gz > $f
sync

tokenize_src_refs $f $l1 $l2 $f_list $ref_cnt


# zcat $f.gz | cut -f1 > $f.$l1
# tokenize_bitext $f $l1

# zcat $f.gz | cut -f2- > $f.$l2
# tokenize_bitext $f $l2

# output: $f.tok.$l1, $f.tok.$l2
#############################################################

# merge_file.pl \
#   $f.gz \
#   $f_list \
#   | perl -nle '
#         (@t)=split(/\t/, $_); 
# 	      print join("\t", @t) if( $t[2] !~ /^\s*$/ && $t[3] !~ /^\s*$/ );
#   ' | gzip - > $f.clean.gz
#   sync

# zcat $f.clean.gz | cut -f3 > $f.tok.clean.$l1
# zcat $f.clean.gz | cut -f4 > $f.tok.clean.$l2
# sync

# rm $f
# sync
#############################################################

