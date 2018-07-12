#!/usr/bin/env bash

IFS=$'\n'

data_path="data/naver/kin/by_user.society"
for d in $(ls -1 ${data_path}) ; do
    echo ${d}

    python3 naver_kin_crawler.py -insert_answer_list \
        -data_path "${data_path}/${d}"
done

data_path="data/naver/kin/by_user.의료"
for d in $(ls -1 ${data_path}) ; do
    echo ${d}

    python3 naver_kin_crawler.py -insert_answer_list \
        -data_path "${data_path}/${d}"
done

data_path="data/naver/kin/by_user.분야별지식인"
for d in $(ls -1 ${data_path}) ; do
    echo ${d}

    python3 naver_kin_crawler.py -insert_answer_list \
        -data_path "${data_path}/${d}"
done

