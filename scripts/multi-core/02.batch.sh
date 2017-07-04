#!/usr/bin/env bash

header="$1"
domain="$2"

# 입력 파라메터 확인
if [ "${header}" == "" ] ; then
    echo "Usage: "$(basename $0)" [입력 파일 헤더, 예) data/nate/text.] [domain, baseball or economy]"
    exit 1
fi

if [ "${domain}" == "" ] ; then
    domain="baseball"
fi

max_line=100000
sentence_index_dir="data/${domain}/sentence_index"

script_path="./scripts/multi-core"

# 월별로 문장 분석
for f_input in $(ls "${header}"*.bz2) ; do
    f_dir=$(dirname ${f_input})
    f_base=$(basename ${f_input})
    f_name=${f_base#*.}
    f_name=${f_name%.*}

    year=${f_name%.*}

    echo "f_input: ${f_input}, f_dir: ${f_dir}, f_name: ${f_name}, year: ${year}"

    # 01. 텍스트에서 문장만 추출
    ${script_path}/multi.sh "extract_sentence" "${f_input}" "${f_dir}/${f_name}.sentence.bz2" ${max_line}
    LC_COLLATE="C" bzcat "${f_dir}/${f_name}.sentence.bz2" | sort -u | bzip2 - > "${f_dir}/${f_name}.unique_sentence.bz2"

    # 02. 중복 문장 제거
    if [ ! -d "${sentence_index_dir}/${year}" ] ; then
        mkdir -p "${sentence_index_dir}/${year}"
    fi
    
    ${script_path}/multi.sh "get_missing_sentence" "${f_dir}/${f_name}.unique_sentence.bz2" "${f_dir}/${f_name}.missing_sentence.bz2" $(nproc) "${sentence_index_dir}/${year}/${f_name}.sqlite3"

    # 03. 형태소 분석/개체명 인식/파싱
    ${script_path}/multi.sh "pre_process" "${f_dir}/${f_name}.missing_sentence.bz2" "${f_dir}/${f_name}.pre_processed.bz2" ${max_line} "dummy" ${domain}

    # 04. 문장 인덱스 생성
    ${script_path}/multi.sh "make_sentence_index" "${f_dir}/${f_name}.pre_processed.bz2" "${sentence_index_dir}/${year}/${f_name}.sqlite3" $(nproc)

    # 05. 분석 결과 병합
    ${script_path}/multi.sh "merge_result" "${f_input}" "${f_dir}/${f_name}.text_pre_processed.bz2" ${max_line} "${sentence_index_dir}/${year}/${f_name}.sqlite3"
done


