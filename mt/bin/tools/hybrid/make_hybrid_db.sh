#!/bin/bash

# lang_list=("ko" "en")

train_log="$1"

if [[ "$train_log" == "" ]] ; then
    echo "Uage: "$(basename "$0")" [train log dir]"
    exit 1
fi

fname_phrase="phrase-table.reduced.gz"
fname_lexprob="lex_prob.db"

# make phrase table db
if [[ ! -f "$train_log/$fname_phrase.db" ]] ; then
    zcat "$train_log/$fname_phrase" \
        | perl -nle '
            ($l1, $l2, $pr) = split(/ \|\|\| /, $_); 
            ($pr) = split(/ /, $pr); 
            print "$l1:$l2\t$pr" ' \
        | toBerkeleyDB.pl -fn "$train_log/$fname_phrase.db" 
    sync

     # zcat $d_model/$d/phrase-table.reduced.gz \
     #    | cut.pl -d "\|\|\|" -f 1 \
     #    | uniq_sort.pl -c \
     #    | gzip - > $d_model/$d/phrase_count.reduced.gz    
fi

# make lex db
if [[ ! -f "$train_log/$fname_lexprob" ]] ; then
    zcat "$train_log/lex.f2e.gz" \
        | perl -nle 's/ /:/; s/ /\t/; print' \
        | toBerkeleyDB.pl -out "$train_log/$fname_lexprob"

    zcat "$train_log/lex.e2f.gz" \
        | perl -nle 's/ /:/; s/ /\t/; print' \
        | toBerkeleyDB.pl -out "$train_log/$fname_lexprob" 
    sync
fi

# make lm db
for lang in ko en ; do
    if [[ ! -f "$train_log/$lang.lm.db" ]] ; then
        fname_lm="$train_log/$lang.lm.gz"

        if [[ ! -f "$fname_lm" ]] ; then
            zcat "$train_log/train.$lang.gz" > "$train_log/train.$lang"
            sync && lmplz -o 5 -S 80% -T /tmp < "$train_log/train.$lang" | gzip - > "$fname_lm"
            sync && rm "$train_log/train.$lang"
        fi
        
        sync && zcat "$fname_lm" | lm2db.pl \
                    -lm "$train_log/$lang.lm.db" \
                    -backoff "$train_log/$lang.backoff.db"
    fi
done
sync

# # extract ibm score
# extract_ibm-score.sh "$train_log" "$train_log/A3.final.gz"

# # get sentence bleu
# src="$train_log/train.ko"
# tst="$train_log/train.ko.out"
# ref="$train_log/train.en"

# zcat "$src.gz" > "$src"
# zcat "$ref.gz" > "$ref"

# moses -threads 12 -f "$train_log/../moses.binary.ini" < "$src" > "$tst"
# sync && mteval.multi.sh "$tst" "$src" "$ref" "$tst.bleu" 24000

# rm "$src" "$ref"
