#!/usr/bin/env bash

index=$1
import_path=$2
done_path=$3
log_path=$4
id_field=$5
hosts=$6

# 경로 생성
mkdir -p "${done_path}" "${log_path}"

# 호스트 등록
declare -a host_list=()
IFS=','
for h in ${hosts} ; do
    host_list[${#host_list[*]}]=${h}
done

max_host=${#host_list[*]}

# 파일 큐 등록
declare -a queue=()
IFS=$'\n'
for f in $(find ${import_path} -name "????-??.json.bz2") ; do
    queue[${#queue[*]}]=${f}
done

# 실행
echo "size: "${#queue[*]}
for (( i=0 ; i<${#queue[*]} ; i+=${max_host} )) ; do
    for (( j=i,k=0 ; j<i+${max_host} ; j++,k++ )) ; do
        if [[ j -ge ${#queue[*]} ]] ; then
            break
        fi

        f=${queue[j]}
        h=${host_list[k]}
        echo "file name: ${f}, host: ${h}"

        bzcat ${f} | \
            ./elasticsearch_utils.py \
                -import_data \
                -host "http://${h}:9200" \
                -index "${index}" \
                -id_field "${id_field}" \
                2>&1 | tee -a "${log_path}/${h}.${index}.log" &
    done
    echo "waiting"
    wait

    for (( j=i ; j<i+${max_host} ; j++ )) ; do
        if [[ j -ge ${#queue[*]} ]] ; then
            break
        fi

        f=${queue[j]}
        f_base=$(basename ${f})
        echo "move: ${f} -> ${done_path}/${f_base}"

        mv "${f}" "${done_path}/${f_base}"
    done
    sync
done

# 나머지 파일 이동
IFS=$'\n'
for f in $(find ${import_path} -name "*.json.bz2") ; do
    f_base=$(basename ${f})
    echo "move: ${f} -> ${done_path}/${f_base}"

    mv "${f}" "${done_path}/${f_base}"
done
