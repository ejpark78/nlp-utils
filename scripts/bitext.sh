#!/usr/bin/env bash

f_input="$1"

work_dir=$(dirname ${f_input})
filename=$(basename ${f_input})

f_name=${filename%.*}

# 탭 형식을 json 형태로 변환
zcat "${work_dir}/${filename}" \
    | python3 NCCorpus.py -to_json -key english,korean \
    | gzip - > "${work_dir}/${f_name}.json.gz" \
    && sync

# 언어별로 문장 추출
zcat "${work_dir}/${f_name}.json.gz" \
    | python3 NCCorpus.py -get_json_value -key english \
    | gzip - > "${work_dir}/${f_name}.en_sentence.gz"

zcat "${work_dir}/${f_name}.json.gz" \
    | python3 NCCorpus.py -get_json_value -key korean \
    | gzip - > "${work_dir}/${f_name}.ko_sentence.gz"
sync

# 형태소 분석
max_line=100000
./scripts/multi.sh "pos_tagging" "${work_dir}/${f_name}.ko_sentence.gz" "${work_dir}/${f_name}.ko_pos_tagged.gz" ${max_line}

zcat "${work_dir}/${f_name}.ko_pos_tagged.gz" \
    | cut -f2 | perl -ple 's/\/[A-Z]+?\+/ /g; s/\/[A-Z]+?( |$)/$1/g;' \
    >  "${work_dir}/${f_name}.ko_pos_tagged.tok"

# 소문자로 치환
zcat "${work_dir}/${f_name}.en_sentence.gz" \
    | perl ${work_dir}/lowercase.perl \
    | gzip - > "${work_dir}/${f_name}.en_sentence_lc.gz"

./scripts/multi.sh "english_pos_tagging" "${work_dir}/${f_name}.en_sentence_lc.gz" "${work_dir}/${f_name}.en_pos_tagged.gz" ${max_line}

zcat "${work_dir}/${f_name}.en_pos_tagged.gz" \
    | cut -f2 | perl -ple 's/\/.+?( |$)/$1/g;' \
    > "${work_dir}/${f_name}.en_pos_tagged.tok"

# 분석 결과 병합
zcat "${work_dir}/${f_name}.ko_pos_tagged.gz" > "${work_dir}/${f_name}.ko_pos_tagged"
zcat "${work_dir}/${f_name}.en_sentence.gz" > "${work_dir}/${f_name}.en_sentence"
zcat "${work_dir}/${f_name}.en_pos_tagged.gz" > "${work_dir}/${f_name}.en_pos_tagged"
sync

wc -l "${work_dir}/${f_name}.ko_pos_tagged" \
    "${work_dir}/${f_name}.ko_pos_tagged.tok" \
    "${work_dir}/${f_name}.en_sentence" \
    "${work_dir}/${f_name}.en_pos_tagged" \
    "${work_dir}/${f_name}.en_pos_tagged.tok"

paste "${work_dir}/${f_name}.ko_pos_tagged" \
    "${work_dir}/${f_name}.ko_pos_tagged.tok" \
    "${work_dir}/${f_name}.en_sentence" \
    "${work_dir}/${f_name}.en_pos_tagged" \
    "${work_dir}/${f_name}.en_pos_tagged.tok" \
    | python3 NCCorpus.py -to_json -key "korean.sentence,korean.pos_tagged,korean.tokened,english.sentence,english.lower,english.pos_tagged,english.tokened" \
    | gzip - > "${work_dir}/${f_name}.pos_tagged.json.gz" \
    && sync

rm "${work_dir}/${f_name}.json.gz" \
    "${work_dir}/${f_name}.ko_sentence.gz" \
    "${work_dir}/${f_name}.ko_pos_tagged" \
    "${work_dir}/${f_name}.ko_pos_tagged.gz" \
    "${work_dir}/${f_name}.ko_pos_tagged.tok" \
    "${work_dir}/${f_name}.en_pos_tagged.gz" \
    "${work_dir}/${f_name}.en_pos_tagged" \
    "${work_dir}/${f_name}.en_sentence_lc.gz" \
    "${work_dir}/${f_name}.en_pos_tagged.tok" \
    "${work_dir}/${f_name}.en_sentence.gz" \
    "${work_dir}/${f_name}.en_sentence"

