#!/bin/bash
#############################################################
# main
#############################################################
# fn=movies.uniq
fn=$1

fn=${fn/\.gz/}

zcat $fn.gz \
  | clean_bitext_code.pl -l1 2 -l2 3 \
  | get_length_threshold.pl -l1 2 -l2 3 \
  > $fn.rate

sync

zcat $fn.gz \
  | clean_bitext_code.pl -l1 2 -l2 3 \
  | cutoff_length.pl -f $fn.rate -l1 2 -l2 3 \
  | gzip - > $fn.clean.gz

sync

#############################################################
