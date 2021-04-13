#!/bin/bash


tst="$1"
src="$2"
ref="$3"
with_sentence_bleu="$4"

# check arguments
if [[ "$tst" == "" ]] || [[ "$src" == "" ]] || [[ "$ref" == "" ]] ; then
    echo -e "Usage: "$(basename "$0")" <tst> <src> <ref> <with sentence bleu optional: yes or empty>" 1>&2;
    exit 1
fi

if [[ ! -f "$tst" ]] || [[ ! -f "$src" ]] ; then
    echo -e "tst: '$tst' or src: '$src' is not exist." 1>&2;
    exit 1
fi

# check empty line
merge_file.pl "$tst" "$src" "$ref"* \
    | perl -nle '
        BEGIN {
        	$line_no = 1;
        }

        ($tst)=split(/\t/, $_);
        $tst =~ s/\s+$//;
        
        if( $tst ne "" ) {
        	print;
        } else {
        	print STDERR "$line_no: $_";
        }

        $line_no++;
        ' \
    > "$tst.clean" \
    2> "$tst.error"
sync

cat "$tst.clean" | cut -f1 > "$tst.tst"
cat "$tst.clean" | cut -f2- > "$tst.merged"
sync

wc -l "$src" "$tst.clean" "$tst.error"
if (( $(wc -l "$tst.error" | cut -d' ' -f1) == 0 )) ; then
    rm "$tst.error"
fi

cut_eval_set.pl -in "$tst.merged"
sync

# run bleu
wrap.pl -type tst -in "$tst.tst" > "$tst.tst.sgm"
wrap.pl -type src -in "$tst.merged.src" > "$tst.src.sgm"
wrap.pl -type ref -in "$tst.merged.ref" > "$tst.ref.sgm"
sync

# get bleu
mteval-v13a.pl -s "$tst.src.sgm" -r "$tst.ref.sgm" -t "$tst.tst.sgm" > "$tst.bleu"

# get sentence bleu
if [[ "$with_sentence_bleu" == "yes" ]] || [[ "$with_sentence_bleu" == "with_sentence" ]] ; then
    "sentence-bleu" "$tst.merged.ref"* < "$tst.tst" > "$tst.bleu_score"
fi

# clean up temp files
sync && rm "$tst.tst" "$tst.merged.src" \
        "$tst.merged.ref"? \
        "$tst.tst.sgm" "$tst.src.sgm" \
        "$tst.ref.sgm" "$tst.merged" \
        "$tst.clean"
sync

# grep bleu
grep ^NIST "$tst.bleu"
