#!/bin/bash
########################################################################


grep ^NIST $(find . -name *.bleu -print) \
  | perl -nle '
     s/.bleu:NIST score = /\t/; 
     s/\s+ BLEU score = /\t/; 
     s/for system "0"/\t/; 

     s/\.(src|tok|ko)/\t/g;
     s/\.\d+\.utf8\.kren//;

     s/^\.\///; 
     s/\//\t/g; 
     s/\t+\./\t/g;

     print'

