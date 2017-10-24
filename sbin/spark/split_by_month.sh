#!/usr/bin/env bash

home="data/lineagem"

dry=""

for input in $(\ls -d ${home}/자유.json.bz2) ; do
    year=$(basename ${input})
    year="${year/.json.bz2/}"

    output="${input/.json.bz2/.by_month}"
    if [ -f "${output}/_SUCCESS" ] ; then
        echo "skip ${input}"
        continue
    fi

    echo ${input} ${output}

    if [ "${dry}" == "" ] ; then
        # 입력 파일 업로드
        input_path=$(dirname ${input})
        hadoop fs -mkdir -p ${input_path}
        hadoop fs -rm -f -skipTrash ${input}
        hadoop fs -put ${input} ${input_path}

        # 이전 결과 파일 삭제
        hadoop fs -rm -r -f -skipTrash ${output}

        # 스파크 실행
        spark-submit \
            --master yarn \
            --deploy-mode client \
            --num-executors 9 \
            --executor-cores 2 \
            --verbose \
            SparkBatchSplitDate.py -filename ${input} -result ${output}

        # 결과 파일 다운로드
        rm -rf ${output} && sync
        hadoop fs -get ${output} ${output}
    fi
done
