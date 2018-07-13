#!/usr/bin/env bash

IFS=$'\n'

data_path="data/naver/kin/tmp/by_user.economy"
for d in $(ls -1 ${data_path}) ; do
    echo ${d}

    python3 naver_kin_crawler.py -detail -index answer_list -match_phrase '{"user_name": "'${d}'"}'
done


#IFS=$'\n'
#
#data_path="data/naver/kin/by_user.economy.done"
#for d in $(ls -1 ${data_path}) ; do
#    echo ${d}
#
#    python3 naver_kin_crawler.py -insert_answer_list \
#        -data_path "${data_path}/${d}"
#done


#for i in {00..11} ; do
#    echo $i
#    python3 naver_kin_crawler.py -insert_detail -filename data/naver/kin/detail/detail2.$i.db &
#done

#for i in {12..23} ; do
#    echo $i
#    python3 naver_kin_crawler.py -insert_detail -filename data/naver/kin/detail/detail2.$i.db &
#done
#wait


#IFS=$'\n'
#
#data_path="data/naver/kin/by_user.society"
#for d in $(ls -1 ${data_path}) ; do
#    echo ${d}
#
#    python3 naver_kin_crawler.py -insert_answer_list \
#        -data_path "${data_path}/${d}"
#done
#
#data_path="data/naver/kin/by_user.의료"
#for d in $(ls -1 ${data_path}) ; do
#    echo ${d}
#
#    python3 naver_kin_crawler.py -insert_answer_list \
#        -data_path "${data_path}/${d}"
#done
#
#data_path="data/naver/kin/by_user.분야별지식인"
#for d in $(ls -1 ${data_path}) ; do
#    echo ${d}
#
#    python3 naver_kin_crawler.py -insert_answer_list \
#        -data_path "${data_path}/${d}"
#done
#
