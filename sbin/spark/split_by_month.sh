#!/usr/bin/env bash

home="data/dump/2nd"

#nate_entertainment 2017 안됨
# -filename data/dump/2nd/daum_baseball/2017.json.bz2 -result data/dump/2nd/daum_baseball/2017.by_month

for dir_name in $(hadoop fs -ls -d ${home}/daum_baseball/ | perl -ple 's/\s+/\t/g' | cut -f8-) ; do
    db_name=$(basename ${dir_name})

    for input in $(ls ${home}/${db_name}/2017.json.bz2) ; do
        year=$(basename ${input})
        year="${year/.json.bz2/}"

        output="${input/.json.bz2/.by_month}"
        echo ${input} ${output}

        # 이전 결과 파일 삭제
        hadoop fs -rm -r -f -skipTrash ${output}

        # 스파크 실행
        spark-submit \
            --master yarn \
            --deploy-mode client \
            --driver-memory 16g \
            --num-executors 18 \
            --executor-cores 2 \
            --verbose \
            SparkBatchSplitDate.py -filename ${input} -result ${output}

        # 결과 파일 다운로드
        rm -rf ${output} && sync
        hadoop fs -get ${output} ${output}
    done
done
