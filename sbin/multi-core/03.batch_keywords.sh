#!/usr/bin/env bash

header="$1"

# 입력 파라메터 확인
if [ "${header}" == "" ] ; then
    echo "Usage: "$(basename $0)" [입력 파일 헤더, 예) data/nate/text.]"
    exit 1
fi

max_line=100000

# 월별로 문장 분석
for f_input in $(ls "${header}"*.text_pre_processed.gz) ; do
    f_dir=$(dirname ${f_input})
    f_base=$(basename ${f_input})

    f_name=${f_base%.*} # remove tail

    year=${f_name%.*} # remove tail
    year=${year%.*} # remove tail

    echo "${f_input} ${f_dir}, ${f_name}, ${year}"

    # 검색기에 데이터 삽입
    if [[ ! -f "${f_dir}/${f_name}.keywords.gz" ]] ; then
        ./scripts/multi.sh "extract_keywords" "${f_input}" "${f_dir}/${f_name}.keywords.gz" ${max_line} && sync
        zcat "${f_dir}/${f_name}.keywords.gz" | python3 NCElastic.py -make_index -index baseball -type ${year}
    fi
done


#for year in {2006..2007} ; do
#    echo -e "\nyear: ${year}"
#    bzcat "data/nate/${year}.text_pre_processed.keywords.bz2" | python3 NCElastic.py -make_index -index baseball -type ${year}
#done
#
