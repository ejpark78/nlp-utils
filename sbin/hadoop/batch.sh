#!/usr/bin/env bash

max_map=90

home="data/nate_baseball"
domain="baseball"

dry=""

for fname in $(ls -r ${home}/????.bz2) ; do
    type_name=$(basename ${fname})
    type_name="${type_name/.bz2/}"

    echo
    echo ${fname}, ${type_name}

    input_path=$(dirname ${fname})

    # 형태소 분석, 개체명 인식, 키워드 추출
    input="${fname}"
    output="${input_path}/${type_name}.pos.bz2"

    echo "Morph: " ${input}, ${output}

    if [ "${dry}" == "" ] && [ ! -f ${output} ] ; then
        mapper="src/NCPreProcess.py -spark_batch -domain ${domain}"
        time ./sbin/hadoop/streaming.sh ${max_map} "${input}" "${output}" "${mapper}" ""
    fi

    # 의존 파서
    input="${output}"
    output="${input_path}/${type_name}.parsed.bz2"

    echo "Parser: " ${input}, ${output}

    if [ "${dry}" == "" ] && [ ! -f ${output} ] ; then
        mapper="java -Xms1g -Xmx1g -jar parser/parser.jar dictionary/model/"
        #time ./sbin/hadoop/streaming.sh ${max_map} "${input}" "${output}" "${mapper}" ""
    fi
done
