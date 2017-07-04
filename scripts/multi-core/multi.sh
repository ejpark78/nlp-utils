#!/usr/bin/env bash

run_type="$1"
input_filename="$2"
output_filename="$3"
max_line="$4"
index_file_name="$5"
domain="$6"

if [ "${max_line}" == "" ] ; then
    max_line=100000
fi

debug="0"

function dump_sqlite {
    local filename="$1"
    local sql_filename="$2"

#    sqlite3 "${filename}" ".dump" > "${sql_filename}"

    echo "BEGIN TRANSACTION;" > "${sql_filename}" && sync

    echo "PRAGMA legacy_file_format = 1;" >> "${sql_filename}"
    echo "PRAGMA temp_store = 2;" >> "${sql_filename}"
    echo "PRAGMA foreign_keys = 0;" >> "${sql_filename}"
    echo "PRAGMA journal_mode = OFF;" >> "${sql_filename}"
    echo "PRAGMA locking_mode = EXCLUSIVE;" >> "${sql_filename}"

    echo "" >> "${sql_filename}"

    for tbl in $(sqlite3 "${filename}" ".table") ; do
        sqlite3 "${filename}" ".schema ${tbl}" | perl -ple 's/CREATE TABLE /CREATE TABLE IF NOT EXISTS /;' >> "${sql_filename}"
    done

    for tbl in $(sqlite3 "${filename}" ".table") ; do
        echo -e ".mode insert ${tbl}\nSELECT * FROM ${tbl};" | sqlite3 "${filename}" >> "${sql_filename}"
    done

    echo "COMMIT;" >> "${sql_filename}"
    sync
}

function grep_error_sentence {
    local filename="$1"
    local result_filename="$2"

    local length_input=$(cat "${filename}" | wc -l)
    local length_output=$(cat "${result_filename}" | wc -l)
    local error_line=$((length_output + 1))

    local offset=$((length_input - error_line))

    if (( ${length_input} > ${length_output} )) && (( ${offset} > 0 )) ; then
        # 에러 문장 저장
        cat "${filename}" | head -n ${error_line} | tail -n 1 >> "${filename}.error"
        cat "${filename}" | head -n ${error_line} | tail -n 1 >> "${result_filename}"
        sync
    fi

    echo ${offset}
}

function single_process {
    local task_type="$1"
    local filename="$2"
    local index_file_name="$3"
    local domain="$4"

    # 결과 파일 삭제 및 빈 결과 파일 생성
    if [ -f "${filename}.result" ] ; then
        rm "${filename}.result"
    fi
    touch "${filename}.result"

    echo "실행 타입: ${task_type}, 파일명: ${filename}"
    if [ "${task_type}" == "extract_text" ] ; then
        cat "${filename}" | python3 NCPreProcess.py -extract_text > "${filename}.result" 2> "${filename}.log"
    fi

    if [ "${task_type}" == "extract_sentence" ] ; then
        cat "${filename}" | python3 NCPreProcess.py -extract_sentence > "${filename}.result"
    fi

    if [ "${task_type}" == "unique_sort" ] ; then
        cat "${filename}" | LC_COLLATE="C" sort -u > "${filename}.result"
    fi

    if [ "${task_type}" == "pre_process" ] ; then
        local total=$(cat "${filename}" | wc -l)
        local offset=${total}
        local max_try=${offset}
        while true ; do
            if (( ${max_try} != ${total} )) ; then
                echo "max_try: ${max_try}, total: ${total}, offset: ${offset}"
            fi

            max_try=$((max_try - 1))
            cat "${filename}" | tail -n ${offset} | python3 NCPreProcess.py -preprocess -domain ${domain} >> "${filename}.pos_tagged" 2>> "${filename}.log" && sync

            offset=$(grep_error_sentence "${filename}" "${filename}.pos_tagged")
            if (( ${offset} < 0 )) || (( ${max_try} < 0 )); then
                break
            fi
        done

        offset=$(cat "${filename}.pos_tagged" | wc -l)
        max_try=${offset}
        while true ; do
            if (( ${max_try} != ${total} )) ; then
                echo "max_try: ${max_try}, total: ${total}, offset: ${offset}"
            fi

            max_try=$((max_try - 1))
            cat "${filename}.pos_tagged" | tail -n ${offset} | java -Xms1g -Xmx1g -jar "parser/parser.jar" "parser/model/" >> "${filename}.result" 2>> "${filename}.log" && sync

            offset=$(grep_error_sentence "${filename}.pos_tagged" "${filename}.result")
            if (( ${offset} < 0 )) || (( ${max_try} < 0 )); then
                break
            fi
        done
    fi

    if [ "${task_type}" == "pos_tagging" ] ; then
        local offset=$(cat "${filename}" | wc -l)
        local max_try=${offset}
        while true ; do
            max_try=$((max_try - 1))
            cat "${filename}" | tail -n ${offset} | python3 NCPreProcess.py -pos_tagging >> "${filename}.result" 2>> "${filename}.log" && sync

            offset=$(grep_error_sentence "${filename}" "${filename}.result")
            if (( ${offset} < 0 )) || (( ${max_try} < 0 )); then
                break
            fi
        done
    fi

    if [ "${task_type}" == "run_parser" ] ; then
        local offset=$(cat "${filename}" | wc -l)
        local max_try=${offset}
        while true ; do
            max_try=$((max_try - 1))
            cat "${filename}" | tail -n ${offset} | java -Xms1g -Xmx1g -jar "parser/parser.jar" "parser/model/" >> "${filename}.result" 2>> "${filename}.log" && sync

            offset=$(grep_error_sentence "${filename}" "${filename}.result")
            if (( ${offset} < 0 )) || (( ${max_try} < 0 )); then
                break
            fi
        done
    fi

    if [ "${task_type}" == "make_sentence_index" ] ; then
        cat "${filename}" | python3 NCPreProcess.py -make_sentence_index -index_file_name "${filename}.sqlite3"
        dump_sqlite "${filename}.sqlite3" "${filename}.result"
    fi

    if [ "${task_type}" == "merge_result" ] ; then
        cat "${filename}" | python3 NCPreProcess.py -merge_result -index_file_name "${index_file_name}" > "${filename}.result"
    fi

    if [ "${task_type}" == "get_clean_document" ] ; then
        cat "${filename}" | python3 NCCorpus.py -get_clean_document > "${filename}.result"
    fi

    if [ "${task_type}" == "get_missing_sentence" ] ; then
        cat "${filename}" | python3 NCPreProcess.py -get_missing_sentence -index_file_name "${index_file_name}" > "${filename}.result"
    fi

    if [ "${task_type}" == "english_pos_tagging" ] ; then
        cat "${filename}" | python3 NCPreProcess.py -english_pos_tagging > "${filename}.result"
    fi

    if [ "${task_type}" == "extract_keywords" ] ; then
        cat "${filename}" | python3 NCNewsKeywords.py > "${filename}.result"
    fi

    if [ "${debug}" == "0" ] ; then
        echo "분석 완료 파일 삭제: ${filename}"
        rm "${filename}"
    fi
}

function split_file {
    local data_dir="$1"
    local filename="$2"
    local fname="$3"
    local tmp_dir="$4"
    local max_line="$5"

    echo "임시 폴더 생성"
    if [ ! -d "${tmp_dir}" ] ; then
        mkdir -p "${tmp_dir}"
    fi

    if [ "$(ls -A ${tmp_dir} 2>/dev/null)" ] ; then
        rm "${tmp_dir}"/*
    fi

    echo "파일분리"
    if [ "$(ls -A ${tmp_dir}/${fname}.part.????? 2>/dev/null)" ] ; then
        rm -f "${tmp_dir}/${fname}.part."?????
        sync
    fi

    echo "${data_dir}/${filename}"
    bzcat "${data_dir}/${filename}" | split -d -a 5 -l${max_line} - "${tmp_dir}/${fname}.part."
    sync
}

function merge_result {
    local fname="$1"
    local tmp_dir="$2"
    local result_file_name="$3"

    local f_ext=${result_file_name##*.}

    sync
    if [ "${debug}" == "0" ] ; then
        echo "임시 파일 삭제"
        rm -f "${tmp_dir}/${fname}.part."?????
    fi

    echo "결과 파일 병합"
    if [ "${f_ext}" == "sqlite3" ] ; then
        cat "${tmp_dir}/${fname}.part."?????.result | sqlite3 "${result_file_name}"
    else
        cat "${tmp_dir}/${fname}.part."?????.result | bzip2 - > "${result_file_name}"
    fi

    local result_fname=${result_file_name%.*}

    if [ "$(ls -A ${tmp_dir}/${fname}.part.?????.error 2>/dev/null)" ] ; then
        cat "${tmp_dir}/${fname}.part."?????.error | bzip2 - > "${result_fname}.error.bz2"
    fi

    if [ "$(ls -A ${tmp_dir}/${fname}.part.?????.log 2>/dev/null)" ] ; then
        cat "${tmp_dir}/${fname}.part."?????.log | bzip2 - > "${result_fname}.log.bz2"
    fi
    sync

    if [ "${debug}" == "0" ] ; then
        echo "임시 로그/결과 파일 삭제"
        rm -f "${tmp_dir}/${fname}.part."?????.result
        rm -f "${tmp_dir}/${fname}.part."?????.log
    fi
    sync
}

function main {
    local task_type="$1"
    local filename="$2"
    local result_file_name="$3"
    local max_line="$4"
    local index_file_name="$5"
    local domain="$6"

    local max_core=$(nproc)

    local f_base=$(basename ${filename})
    local f_dir=$(dirname ${filename})

    local tmp_dir="${f_dir}/tmp"

    local f_name=${f_base%.*}

    local f_length=$(bzcat "${filename}" | wc -l)
    local max_core_length=$((f_length / max_core + 1))

    if (( ${max_line} > ${max_core_length} )) || (( ${max_line} == ${max_core} )) ; then
        echo "코어 수 만큼 파일 분리"
        max_line=${max_core_length}
    fi

    echo "파일 분리: ${f_dir}, ${f_base}, ${f_name}, ${f_name}, ${tmp_dir}, max_line: ${max_line}, f_length: ${f_length}"
    split_file "${f_dir}" "${f_base}" "${f_name}" "${tmp_dir}" "${max_line}"

    echo "분리된 파일 목록 생성"
    declare -a file_list=()
    for single_filename in $(ls "${tmp_dir}/${f_name}.part."????? 2>/dev/null) ; do
        file_list[${#file_list[*]}]=${single_filename}
    done

    echo "분석 시작: "${#file_list[*]}
    for (( i=0 ; i<${#file_list[*]} ; i+=${max_core} )) ; do
        for (( j=i ; j<i+${max_core} ; j++ )) ; do
            if [[ j -ge ${#file_list[*]} ]] ; then
                break
            fi

            time single_process "${task_type}" "${file_list[j]}" "${index_file_name}" "${domain}" &
        done

        echo "waiting"
        wait
    done

    echo "최종 결과 생성: ${f_name} ${tmp_dir} ${result_file_name}"
    merge_result "${f_name}" "${tmp_dir}" "${result_file_name}"
}

# ${input_filename} 가 파일일 경우: 큰 파일 하나를 받아서 여러개로 분리 & 분석
echo -e "\n# 분석 시작: ${run_type} ${input_filename} ${output_filename} ${max_line} ${index_file_name} ${domain}\n\n"
main "${run_type}" "${input_filename}" "${output_filename}" "${max_line}" "${index_file_name}" "${domain}"

# 파일 헤더를 입력 받아서 개별 파일 분석
