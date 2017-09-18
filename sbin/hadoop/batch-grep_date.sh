#!/usr/bin/env bash

max_map=90

home="data/dump/by_date"

for dir_name in $(ls -d ${home}/*/) ; do
    echo ${dir_name}
    db_name=$(basename ${dir_name})

    for filename in $(ls ${home}/${db_name}/2017.json.bz2) ; do
        echo ${db_name} ${filename}
        fname=$(basename ${filename})
        year="${fname/.json.bz2/}"

        echo ${db_name}, ${year}, ${fname}

        job_name="${dir_name}, ${db_name}, ${year}"

        # 결과 폴더: 로컬 저장소
        result_dir="data/dump/by_date2/${db_name}"
        if [ ! -d ${result_dir} ] ; then
            mkdir -p "${result_dir}"
        fi

        # 입력 파일 업로드 폴더: 하둡 저장소
        corpus_dir="/user/ejpark/corpus/by_date/${db_name}"
        hadoop fs -mkdir -p ${corpus_dir}

        input="${corpus_dir}/${fname}"
        output="${result_dir}/${fname}"

        # 1. 업로드
        hadoop fs -rm -r -f -skipTrash "${corpus_dir}/${fname}"
        hadoop fs -put "${home}/${db_name}/${fname}" "${input}"

        # 2. 분리 스크립트 실행
        mapper="grep ^2017-09"
        time ./sbin/hadoop/streaming.sh ${max_map} "${input}" "${output}" "${mapper}" "" "${job_name}"

        # 완료 파일 이동
        done_dir="data/dump/done/${db_name}"
        if [ ! -d ${done_dir} ] ; then
            mkdir -p "${done_dir}"
        fi
        mv ${filename} ${done_dir}/
    done
done
