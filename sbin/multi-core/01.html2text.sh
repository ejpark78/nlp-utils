#!/usr/bin/env bash

filename="$1"
result_dir="$2"

# 입력 파라메터 확인
if [ "${filename}" == "" ] || [ "${result_dir}" == "" ] ; then
    echo "Usage: "$(basename $0)" [입력 파일명] [출력 경로]"
    exit 1
fi

max_line=100000

# 파일 확장자 제거
f_name=${filename%.*}
# json 테그 제거
f_name=${f_name%.*}

script_path="./scripts/multi-core"

if [ ! -d "${result_dir}" ] ; then
    mkdir -p ${result_dir}
fi

# 01. html 에서 텍스트 추출
${script_path}/multi.sh "extract_text" "${filename}" "${f_name}.text.bz2" ${max_line} && sync

# 02. 월별 분리
bzcat "${f_name}.text.bz2" | python3 NCPreProcess.py -split_by_month -header "${result_dir}/text." && sync
