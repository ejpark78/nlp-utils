#!/bin/bash
#############################################################
# eval

ini_fp=$1
ini_pe=$2

src=$3
ref=$4
tag=$5

tst=$src.out
tst_pivot=$src.pivot
#############################################################
if [ "$ini_fp" == "clean" ];then
    echo "clean"
    echo ""

    rm *.sgm; sync

    exit 0
fi
#############################################################
echo -e "ini_fp: $ini_fp"
echo -e "ini_pe: $ini_pe"
echo -e "src: $src"
echo -e "ref: $ref"
echo -e "tag: $tag"
echo ""
echo -e "tst: $tst"
echo -e "tst_pivot: $tst_pivot"
echo ""
#############################################################
# transfer

moses -f $ini_fp -threads 12 -i $src > $tst_pivot
sync

moses -f $ini_pe -threads 12 -i $tst_pivot > $tst
sync

wrap.pl -type src -in $src -out $src.sgm
wrap.pl -type tst -in $tst -out $tst.sgm
wrap.pl -type ref -in $ref -out $ref.sgm
sync

mteval-v13a.pl -s $src.sgm -r $ref.sgm -t $tst.sgm > $src.bleu
sync

grep ^NIST $src.bleu

echo DONE
#############################################################
