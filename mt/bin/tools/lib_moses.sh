#!/bin/bash
crf_model="$TOOLS/model/tagger/ko/model.syllpostagger.ap.crfsuite"


function gunzip_file {
    local in_file="$1"

    local org_in_file=""
    if [[ $(file "--mime-type" "$in_file" | cut -d' ' -f2) == "application/gzip" ]] ; then
        zcat "$in_file" > "$in_file.unzip"
        sync

        org_in_file="$in_file"
        in_file="$in_file.unzip"
    fi

    echo -e "$in_file\t$org_in_file"
}


function mteval {
    local mteval_tst="$1"
    local mteval_src="$2"
    local mteval_ref="$3"

    #echo -e "# mteval src: $mteval_src, ref: $mteval_ref, tst: $mteval_tst" 1>&2

    wrap.pl -type src -in "$mteval_src" -out "$mteval_src.sgm"
    wrap.pl -type ref -in "$mteval_ref" -out "$mteval_ref.sgm"
    wrap.pl -type tst -in "$mteval_tst" -out "$mteval_tst.sgm"

    sync && mteval-v13a.pl \
                -s "$mteval_src.sgm" \
                -r "$mteval_ref.sgm" \
                -t "$mteval_tst.sgm" \
                > "$mteval_tst.bleu"

    sync && rm "$mteval_src" "$mteval_ref" "$mteval_tst" \
                "$mteval_src.sgm" "$mteval_ref.sgm" "$mteval_tst.sgm"
    sync
}


function split_mteval {
    local mteval_tst="$1"
    local mteval_src="$2"
    local mteval_ref="$3"
    local mteval_bleu="$4"
    local max_core="$5"
    
    echo -e "split_mteval: \nmteval_tst: $mteval_tst\n, mteval_src: $mteval_src\n, mteval_ref: $mteval_ref\n, max_core: $max_core" 1>&2

    split.sent.sh "$mteval_src" $max_core "$mteval_src.core." 2>/dev/null
    split.sent.sh "$mteval_ref" $max_core "$mteval_ref.core." 2>/dev/null
    split.sent.sh "$mteval_tst" $max_core "$mteval_tst.core." 2>/dev/null
    sync

    for (( i=0 ; i<$max_core ; i++ )) ; do
        local c=$(printf '%02d' $i)
        # mteval "$mteval_tst.core.$c" "$mteval_src.core.$c" "$mteval_ref.core.$c" &
        "sentence-bleu" "$mteval_ref.core.$c"* < "$mteval_tst.core.$c" > "$mteval_tst.core.$c.bleu" &
    done

    wait
    sync

    # merge
    if [[ -f "$mteval_out" ]] ; then
        rm "$mteval_out"
        sync
    fi

    for (( i=0 ; i<$max_core ; i++ )) ; do
        local c=$(printf '%02d' $i)

        # cat "$mteval_tst.core.$c.bleu" | grep "^# Sentence BLEU:" | cut -f2- >> "$mteval_tst.bleu"
        cat "$mteval_tst.core.$c.bleu" >> "$mteval_bleu"
        sync && rm "$mteval_tst.core.$c.bleu"
    done
    sync
}


function tagging_ko() {
    local in_tagging_ko="$1"
    local out_tagging_ko="$2"

    echo -e "tagging_ko, in_tagging_ko: '$in_tagging_ko', out_tagging_ko: '$out_tagging_ko'" 1>&2

    cat "$in_tagging_ko" \
        | "$TOOLS/tagging_ko" "$crf_model" \
        > "$out_tagging_ko"
    sync
}


tokenize_cn() {
    echo -e "## tokenize_cn\n" 1>&2
    
    # export CLASSPATH=~/workspace/tools/bin/stanford-segmenter-2015-12-09
    # sudo add-apt-repository ppa:webupd8team/java -y
    # sudo apt-get update
    # sudo apt-get install oracle-java8-installer
    
    # sudo apt-get install oracle-java8-set-default

    in_tokenize_cn="$1"
    out_tokenize_cn="$2"

    java -mx2g -cp "$TOOLS_HOME/stanford-segmenter/*" edu.stanford.nlp.ie.crf.CRFClassifier \
        -sighanCorporaDict "$TOOLS_HOME/stanford-segmenter/data" \
        -textFile "$in_tokenize_cn" \
        -inputEncoding UTF-8 \
        -sighanPostProcessing true \
        -keepAllWhitespaces false \
        -loadClassifier "$TOOLS_HOME/stanford-segmenter/data/ctb.gz" \
        -serDictionary "$TOOLS_HOME/stanford-segmenter/data/dict-chris6.ser.gz" \
        > "$out_tokenize_cn"

    sync
}


function tagging_file_multi {
    local lang="$1"
    local in_file="$2"
    local out_file="$3"
    local max_core="$4"
    local column="$5"

    if [[ "$lang" == "" ]] ; then
        lang="ko"
    fi

    # check column
    local org_in_file=""
    if (( "$column" != -1 )) ; then
        cat "$in_file" | cut -f $column > "$in_file.column"
        sync

        org_in_file="$in_file"
        in_file="$in_file.column"
    fi

    # check length
    local len=$(wc -l "$in_file" | cut -d' ' -f1)

    # tagging
    if (( "$len" > "$max_core" )) ; then
        split.sent.sh "$in_file" $max_core "$in_file.core." && sync

        for (( i=0 ; i<$max_core ; i++ )) ; do
            {
                local c=$(printf '%02d' $i)

                local input="$in_file.core.$c"
                local output="$out_file.core.$c"
                
                if [[ "$lang" == "ko" ]] ; then
                    tagging_ko "$input" "$output"
                elif [[ "$lang" == "cn" ]] ; then
                    tokenize_cn "$input" "$output"
                else
                    cat "$input" | tokenizer.perl -q -l $lang | convert_code.pl > "$output" 
                fi
            } &
        done

        wait
        sync

        # merge
        for (( i=0 ; i<$max_core ; i++ )) ; do
            local c=$(printf '%02d' $i)
            cat "$out_file.core.$c" >> "$out_file"
            sync

            rm "$in_file.core.$c" "$out_file.core.$c"
        done
    else
        if [[ "$lang" == "ko" ]] ; then
            tagging_ko "$in_file" "$out_file"
        elif [[ "$lang" == "cn" ]] ; then
            tokenize_cn "$in_file" "$out_file"
        else
            cat "$in_file" | tokenizer.perl -q -l $lang | convert_code.pl > "$out_file"
        fi
    fi
    sync

     # delete unzip file
    if [[ -f "$org_in_file" ]] ; then
        # merge
        merge_file.pl "$org_in_file" "$out_file" > "$out_file.tmp"
        sync && mv "$out_file.tmp" "$out_file"

        rm "$in_file"
        sync
    fi
}


# tokenize_fr() {
#     echo -e "## tokenize_fr\n" 1>&2

#     in_tokenize_fr=$1
#     out_tokenize_fr=$2

#     # spanish tokenize

#     cat "$in_tokenize_fr" \
#         | perl "$TOOLS/scripts/tokenizer.perl" -l en \
#         > "$in_tokenize_fr.tok"

#     perl "$TOOLS/mosesdecoder/scripts/lowercase.perl" \
#         < "$in_tokenize_fr.tok" \
#         > "$out_tokenize_fr"

#     sync
# }


# tokenize_es() {
#     echo -e "## tokenize_es: use spanish TreeTagger\n" 1>&2

#     in_tokenize_es="$1"
#     out_tokenize_es="$2"

#     # spanish tokenize
#     treetagger_home="$TOOLS/TreeTagger"

#     cat "$in_tokenize_es" \
#         | perl "$TOOLS/tree-tagger-spanish-utf8.pl" -TOOLS "$TOOLS" \
#         > "$out_tokenize_es"

#     sync
# }



# tokenize_en() {
#     echo -e "## tokenize_en\n" 1>&2

#     in_tokenize_en="$1"
#     out_tokenize_en="$2"

#     echo -e "# in_tokenize_en:$in_tokenize_en\n"
#     echo -e "# out_tokenize_en:$out_tokenize_en\n\n"

#     java -mx2048m -Xms3072M -Xmx4096M \
#         -cp "$TOOLS/stanford-postagger-full-2013-04-04/stanford-postagger.jar" edu.stanford.nlp.tagger.maxent.MaxentTagger \
#         -XX:+AggressiveHeap -jar jarfile \
#         -model "$TOOLS/stanford-postagger-full-2013-04-04/models/wsj-0-18-bidirectional-nodistsim.tagger" \
#         -textFile "$in_tokenize_en" \
#         -sentenceDelimiter newline -tokenize true \
#         > "$in_tokenize_en.tagged"

#     sync

#     echo -e "# remove tag info.\n"
#     cat "$in_tokenize_en.tagged" \
#         | perl "$TOOLS/remove_eng_postag.pl" \
#         > "$in_tokenize_en.tagged.tok"

#     sync

#     perl "$TOOLS/mosesdecoder/scripts/lowercase.perl" \
#         < "$in_tokenize_en.tagged.tok" \
#         > "$out_tokenize_en"

#     sync
# }


# tokenize_ko() {
#     echo -e "## tokenize_ko\n" 1>&2

#     in_tokenize_ko=$1
#     out_tokenize_ko=$2

#     echo -e "# in_tokenize_ko:$in_tokenize_ko\n"
#     echo -e "# out_tokenize_ko:$out_tokenize_ko\n\n"

#     cat "$in_tokenize_ko" \
#         | perl "$TOOLS/prepare_seg.pl" \
#         | python "$TOOLS/ETRIKSegmenter.py" \
#         > "$in_tokenize_ko.crfsuite"

#     sync

#     crfsuite tag \
#         -m "$crf_model" \
#         "$in_tokenize_ko.crfsuite" \
#         > "$in_tokenize_ko.crf_out"

#     sync

#     cat "$in_tokenize_ko" \
#         | perl "$TOOLS/prepare_seg.pl" \
#         > "$in_tokenize_ko.prepare_out"

#     sync

#     cat "$in_tokenize_ko.prepare_out" \
#         | perl "$TOOLS/post_seg.pl" \
#              -plan_text \
#              -s "$in_tokenize_ko.crf_out" \
#              > "$out_tokenize_ko"

#     sync
# }


# tokenize_file() {
#     echo -e "## tokenize_file\n" 1>&2

#     lang_tokenize_file="$1"
#     in_tokenize_file="$2"
#     out_tokenize_file="$3"

#     echo -e "# in_tokenize_file: $in_tokenize_file"
#     echo -e "# lang_tokenize_file: $lang_tokenize_file"
#     echo -e "# out_tokenize_file: $out_tokenize_file"

#     if [ "$lang_tokenize_file" = "fr" ]; then
#         tokenize_fr "$in_tokenize_file" "$out_tokenize_file"
#     fi

#     if [ "$lang_tokenize_file" = "es" ]; then
#         tokenize_es "$in_tokenize_file" "$out_tokenize_file"
#     fi

#     if [ "$lang_tokenize_file" = "ko" ]; then
#         tokenize_ko "$in_tokenize_file" "$out_tokenize_file"
#     fi

#     if [ "$lang_tokenize_file" = "en" ]; then
#         tokenize_en "$in_tokenize_file" "$out_tokenize_file"
#     fi

#     if [ "$lang_tokenize_file" = "cn" ]; then
#         tokenize_cn "$in_tokenize_file" "$out_tokenize_file"
#     fi
# }


# function tagging_file() {
#     local lang_tagging_file="$1"
#     local in_tagging_file="$2"
#     local out_tagging_file="$3"
#     local opt_tagging_file="$4"

#     echo -e "## tagging_file" 1>&2
#     echo -e "# in_tagging_file: '$in_tagging_file', lang_tagging_file: '$lang_tagging_file', out_tagging_file: '$out_tagging_file'" 1>&2

#     if [ "$lang_tagging_file" = "fr" ]; then
#         tokenize_fr "$in_tagging_file" "$out_tagging_file"
#     fi

#     if [ "$lang_tagging_file" = "es" ]; then
#         tokenize_es "$in_tagging_file" "$out_tagging_file"
#     fi

#     if [ "$lang_tagging_file" = "ko" ]; then
#         tagging_ko "$in_tagging_file" "$out_tagging_file"

#         if [ "$opt_tagging_file" = "without_tag" ]; then
#             echo -e "# remove pos tag" 1>&2

#             mv "$out_tagging_file" "$out_tagging_file.pos_tag"
#             sync

#             cat "$out_tagging_file.pos_tag" \
#             | "$TOOLS/smt/remove_pos_tag.pl" \
#             > "$out_tagging_file"
#             sync
#         fi
#     fi

#     if [ "$lang_tagging_file" = "en" ]; then
#         tokenize_en "$in_tagging_file" "$out_tagging_file"
#     fi

#     if [ "$lang_tagging_file" = "cn" ]; then
#         tokenize_cn "$in_tagging_file" "$out_tagging_file"
#     fi
# }




# prepare_train_data() {
#     echo -e "## prepare_data\n" 1>&2

#     in_prepare_data="$1"
#     file_name="$2"
#     src="$3"
#     trg="$4"
#     out_dir="$5"
#     out_prepare_data="$6"

#     echo -e "# in_prepare_data: $in_prepare_data" 1>&2
#     echo -e "# file_name: $file_name" 1>&2
#     echo -e "# src: $src" 1>&2
#     echo -e "# trg: $trg" 1>&2
#     echo -e "# out_dir: $out_dir" 1>&2
#     echo -e "# out_prepare_data: $out_prepare_data" 1>&2

#     cp "$in_prepare_data" "$out_dir/"
#     cp "$in_prepare_data" "$out_dir/$file_name"

#     sync

#     cut -f1 "$out_dir/$file_name" > "$out_dir/$file_name.src.$src"
#     cut -f2 "$out_dir/$file_name" > "$out_dir/$file_name.trg.$trg"

#     sync

#     echo -e "# clean (cut off long sentences)\n" 1>&2
#     perl "$TOOLS/my-clean-corpus-n.perl" \
#         "$out_dir/$file_name.src.$src" "$out_dir/$file_name.trg.$trg" \
#         "$src" "$trg" \
#         "$out_dir/$file_name.clean.src" \
#         "$out_dir/$file_name.clean.trg" \
#         1 40

#     sync

#     perl "$TOOLS/merge_file.pl" \
#         "$out_dir/$file_name.clean.src" \
#         "$out_dir/$file_name.clean.trg" \
#         > "$out_dir/$file_name.clean"

#     sync

#     cut -f1 "$out_dir/$file_name.clean" > "$out_dir/$file_name.clean.src.$src"
#     cut -f2 "$out_dir/$file_name.clean" > "$out_dir/$file_name.clean.trg.$trg"

#     sync

#     echo -e "# tagging_file" 1>&2
#     tagging_file \
#         "$src" \
#         "$out_dir/$file_name.clean.src.$src" \
#         "$out_dir/$file_name.clean.src.$src.tok" \
#         "without_tag"

#     tagging_file \
#         "$trg" \
#         "$out_dir/$file_name.clean.trg.$trg" \
#         "$out_dir/$file_name.clean.trg.$trg.tok" \
#         "without_tag"

#     sync 

#     perl "$TOOLS/merge_file.pl" \
#          "$out_dir/$file_name.clean.src.$src.tok" \
#          "$out_dir/$file_name.clean.trg.$trg.tok" \
#          > "$out_prepare_data"

#      sync
# }


# prepare_test_data() {
#     # for test
#     echo -e "## prepare_test_data\n" 1>&2

#     in_prepare_test_data="$1"
#     file_name="$2"
#     src="$3"
#     trg="$4"
#     out_dir="$5"
#     out_prepare_test_data="$6"

#     echo "# in_prepare_test_data: $in_prepare_test_data"
#     echo "# file_name: $file_name"
#     echo "# src: $src"
#     echo "# trg: $trg"
#     echo "# out_dir: $out_dir"
#     echo "# out_prepare_test_data: $out_prepare_test_data"

#     cp "$in_prepare_test_data" "$out_dir/$file_name"

#     sync

#     tmp_ref=$RANDOM
#     mkdir -p "$out_dir/$tmp_ref"

#     sync

#     perl "$TOOLS/bin/cut_each_columns.pl" \
#         -fn "$out_dir/$file_name" \
#         -prefix "$out_dir/$tmp_ref/$file_name."

#     # rename src
#     mv "$out_dir/$tmp_ref/$file_name.0" "$out_dir/$file_name.clean.src.$src"

#     sync

#     echo -e "# tokenize: $src\n" 1>&2
#     tagging_file \
#         "$src" \
#         "$out_dir/$file_name.clean.src.$src" \
#         "$out_dir/$file_name.clean.src.$src.tok" \
#         "without_tag"

#     echo -e "# tokenize: $trg\n" 1>&2 1>&2
#     file_list="$out_dir/$file_name.clean.src.$src.tok"
#     for fn in "$out_dir/$tmp_ref/$file_name."*
#     do
#         echo "$fn"
#         tagging_file \
#             "$trg" \
#             "$fn" \
#             "$fn.clean.trg.$trg.tok" \
#             "without_tag"

#         file_list=$file_list" $fn.clean.trg.$trg.tok"
#     done

#     echo -e "FILE_LIST: $file_list" 1>&2

#     perl "$TOOLS/merge_file.pl" \
#          $file_list \
#          > "$out_prepare_test_data"

#     mv "$out_dir/$tmp_ref/*.*" "$out_dir/"
#     sync

#     rm -rf "$out_dir/$tmp_ref"
#     sync
# }


# train_moses() {
#     echo -e "## train_moses\n" 1>&2

#     in_moses_train="$1"
#     src=$2
#     trg=$3
#     out_train_moses_dir="$4"

#     echo -e "# in_moses_train: $in_moses_train" 1>&2
#     echo -e "# src: $src" 1>&2
#     echo -e "# trg: $trg" 1>&2
#     echo -e "# out_train_moses_dir: $out_train_moses_dir\n" 1>&2

#     mkdir -p "$out_train_moses_dir/data"

#     cp "$in_moses_train" "$out_train_moses_dir/data/train.$src-$trg"

#     cut -f1 "$out_train_moses_dir/data/train.$src-$trg" > "$out_train_moses_dir/data/train.$src-$trg.$src.f"
#     cut -f2 "$out_train_moses_dir/data/train.$src-$trg" > "$out_train_moses_dir/data/train.$src-$trg.$trg.e"

#     sync

#     echo -e "# build LM" 1>&2
#     ## KenLM
#     "$TOOLS/mosesdecoder/bin/lmplz -o 5 -S 80% -T /tmp " \
#         "< $out_train_moses_dir/data/train.$src-$trg.$trg.e" \
#         "> $out_train_moses_dir/train.$src-$trg.$trg.lm"

#     "$TOOLS/mosesdecoder/bin/build_binary " \
#         " $out_train_moses_dir/train.$src-$trg.$trg.lm" \
#         " $out_train_moses_dir/train.$src-$trg.$trg.lm.binary"

#     ## SRILM
#     # "$TOOLS/srilm/bin/i686-m64/ngram-count" \
#     #     -order 3 \
#     #     -interpolate \
#     #     -kndiscount \
#     #     -unk \
#     #     -text "$out_train_moses_dir/data/train.$src-$trg.$trg.e" \
#     #     -lm "$out_train_moses_dir/train.$src-$trg.$trg.lm"

#     sync

#     mkdir -p "$out_train_moses_dir/corpus" \
#                 "$out_train_moses_dir/giza.f-e" \
#                 "$out_train_moses_dir/giza.e-f"

#     echo -e "# train moses" 1>&2
#     perl "$TOOLS/mosesdecoder/scripts/training/train-model.perl" \
#         -external-bin-dir "$TOOLS/bin" \
#         -mgiza -mgiza-cpus 12 \
#         -parallel -cores 12 \
#         -sort-buffer-size 10G -sort-batch-size 253 \
#         -sort-compress gzip -sort-parallel 12 \
#         -root-dir "$out_train_moses_dir" \
#         -model-dir "$out_train_moses_dir" \
#         -giza-f2e "$out_train_moses_dir/giza.f-e" \
#         -giza-e2f "$out_train_moses_dir/giza.e-f" \
#         -corpus-dir "$out_train_moses_dir/corpus" \
#         -corpus "$out_train_moses_dir/data/train.$src-$trg" \
#         -f $src.f \
#         -e $trg.e \
#         -alignment grow-diag-final-and \
#         -reordering msd-bidirectional-fe \
#         -lm "0:5:$out_train_moses_dir/train.$src-$trg.$trg.lm.binary:8"

#         # -scripts-root-dir "$TOOLS/mosesdecoder/scripts" \

#     sync

#     echo -e "# pruning phrase-table" 1>&2
#     zcat "$out_train_moses_dir/phrase-table.gz" \
#         | "$TOOLS/mosesdecoder/scripts/training/threshold-filter.perl" 0.0001 \
#         | gzip - > "$out_train_moses_dir/phrase-table.reduced.gz"

#     zcat "$out_train_moses_dir/reordering-table.wbe-msd-bidirectional-fe.gz" \
#         | perl "$TOOLS/mosesdecoder/scripts/training/remove-orphan-phrase-pairs-from-reordering-table.perl" \
#              "$out_train_moses_dir/phrase-table.reduced.gz" \
#         | gzip - > "$out_train_moses_dir/reordering-table.wbe-msd-bidirectional-fe.reduced.gz"

#     sync

#     echo -e "# convert phrase-table binary" 1>&2
#     "$TOOLS/mosesdecoder/bin/processPhraseTable" \
#         -threads 8 \
#         -ttable 0 0 "$out_train_moses_dir/phrase-table.reduced.gz" \
#         -nscores 5 -out "$out_train_moses_dir/phrase-table"

#     "$TOOLS/mosesdecoder/bin/processLexicalTable" \
#         -threads 8 \
#         -in "$out_train_moses_dir/reordering-table.wbe-msd-bidirectional-fe.reduced.gz" \
#         -out "$out_train_moses_dir/reordering-table"

#     sync
# }


# train_giza() {
#     echo -e "## train_giza\n" 1>&2

#     model_path="$1"
#     data_path="$2"
#     train_set="$3"

#     sync

#     # train moses
#     perl "$TOOLS/mosesdecoder/scripts/training/train-model.perl" \
#         --first-step 1 \
#         --last-step 6 \
#         -external-bin-dir "$TOOLS/bin" \
#         -mgiza -mgiza-cpus 8 \
#         -scripts-root-dir "$TOOLS/mosesdecoder/scripts" \
#         -root-dir "$home" \
#         -model-dir "$model_path" \
#         -giza-f2e "$model_path/giza.$src-$trg" \
#         -giza-e2f "$model_path/giza.$trg-$src" \
#         -corpus-dir "$model_path/corpus" \
#         -corpus "$data_path/$train_set.$src-$trg" \
#         -f $src \
#         -e $trg \
#         -alignment grow-diag-final-and \
#         -reordering msd-bidirectional-fe \
#         -lm "0:3:$model_path/$train_set.$src-$trg.$trg.lm"

#     sync
# }


# run_moses() {
#     echo -e "## run_moses\n" 1>&2

#     moses_model_path="$1"
#     src=$2
#     trg=$3
#     in_run_moses="$4"
#     out_run_moses="$5"

#     echo -e "# moses_model_path: $moses_model_path" 1>&2
#     echo -e "# src: $src" 1>&2
#     echo -e "# trg: $trg" 1>&2
#     echo -e "# in_run_moses: $in_run_moses" 1>&2
#     echo -e "# out_run_moses: $out_run_moses\n" 1>&2

#     cut -f1 "$in_run_moses" > "$in_run_moses.$src.f"
#     cut -f2 "$in_run_moses" > "$in_run_moses.$trg.e"

#     "$TOOLS/mosesdecoder/bin/moses" \
#         -config "$moses_model_path/moses.ini" \
#         -input-file "$in_run_moses.$src.f" \
#         -threads 8 \
#         1> "$out_run_moses" 
#         # \
#         # 2> "$out_run_moses.log"

#     sync

#     # cat "$out_run_moses.log" \
#     #     | get_moses_trans_time.pl \
#     #     > "$out_run_moses.trans_time"

#     sync
# }


# run_moses_detoken() {
#     echo -e "## run_moses_detoken\n" 1>&2

#     moses_detoken_model_path="$1"
#     src=$2
#     trg=$3
#     in_run_moses_detoken="$4"
#     out_run_moses_detoken="$5"

#     echo -e "# moses_detoken_model_path: $moses_detoken_model_path"
#     echo -e "# src: $src"
#     echo -e "# trg: $trg"
#     echo -e "# in_run_moses_detoken: $in_run_moses_detoken"
#     echo -e "# out_run_moses_detoken: $out_run_moses_detoken\n"

#     cut -f1 "$in_run_moses_detoken" > "$in_run_moses_detoken.$src"

#     "$TOOLS/mosesdecoder/bin/moses" \
#         -config "$moses_detoken_model_path/moses.ini" \
#         -input-file "$in_run_moses_detoken.$src" \
#         -threads 8 \
#         1> "$out_run_moses_detoken" 

#     sync
# }


# run_bleu() {
#     echo -e "## run_bleu\n" 1>&2
    
#     source_run_bleu="$1"
#     src=$2
#     trg=$3
#     in_run_bleu="$4"
#     out_run_blue="$5"

#     echo -e "# source_run_bleu: $source_run_bleu" 1>&2
#     echo -e "# src: $src" 1>&2
#     echo -e "# trg: $trg" 1>&2
#     echo -e "# in_run_bleu: $in_run_bleu" 1>&2
#     echo -e "# out_run_blue: $out_run_blue" 1>&2

#     cut -f1 "$source_run_bleu" > "$source_run_bleu.$src.f"
#     cut -f2- "$source_run_bleu" > "$source_run_bleu.$trg.e"

#     perl "$TOOLS/bin/cut_each_columns.pl" \
#         -fn "$source_run_bleu.$trg.e" \
#         -prefix "$source_run_bleu.$trg.e"

#     rm "$source_run_bleu.$trg.e"

#     perl "$TOOLS/wrap.pl" \
#         -type src \
#         -in "$source_run_bleu.$src.f" \
#         -out "$source_run_bleu.$src.f.sgm"

#     perl "$TOOLS/wrap.pl" \
#         -type ref \
#         -in "$source_run_bleu.$trg.e" \
#         -out "$source_run_bleu.$trg.e.sgm"

#     perl $TOOLS/wrap.pl \
#         -type tst \
#         -in "$in_run_bleu" \
#         -out "$in_run_bleu.sgm"

#     sync

#     perl "$TOOLS/mosesdecoder/scripts/mteval-v13a.pl" \
#         --no-smoothing \
#         -s "$source_run_bleu.$src.f.sgm" \
#         -r "$source_run_bleu.$trg.e.sgm" \
#         -t "$in_run_bleu.sgm" \
#         > "$out_run_blue"

#     sync

#     grep ^NIST "$out_run_blue"
# }


# run_sent_bleu() {
#     echo -e "## run_sent_bleu\n" 1>&2

#     src_run_sent_bleu="$1"
#     ref_run_sent_bleu="$2"
#     tst_run_sent_bleu="$3"
#     org_run_sent_bleu="$4"
#     out_run_sent_bleu="$5"

#     sync 
    
#     cut -f2- "$org_run_sent_bleu" > "$ref_run_sent_bleu"

#     sync    

#     # sentence blue
#     perl "$TOOLS/prepare_sent_bleu.pl" \
#         -src "$src_run_sent_bleu" \
#         -tst "$tst_run_sent_bleu" \
#         -ref "$ref_run_sent_bleu" \
#         | perl "$TOOLS/sent_bleu.pl" \
#         > "$tst_run_sent_bleu.sent_bleu"

#     sync

#     grep -v ^# "$tst_run_sent_bleu.sent_bleu" \
#         > "$tst_run_sent_bleu.sent_bleu.clean"

#     sync

#     perl "$TOOLS/merge_file.pl" \
#         "$tst_run_sent_bleu.sent_bleu.clean" \
#         "$org_run_sent_bleu" \
#         > "$out_run_sent_bleu"

#     sync
# }


# clean_data() {
#     echo -e "## clean_data\n" 1>&2

#     for i in $(seq 0 9); do 
#         rm -rf "$data/train.$i.$src-$trg*"
#         rm -rf "$data/test.$i.$src-$trg*"
#         rm -rf "$data/data.$src-$trg.$src"
#         rm -rf "$data/data.$src-$trg.$trg"
#         rm -rf "$data/data.$src-$trg.clean*"
#     done

#     sync
# }
