#!/usr/bin/env bash

IFS=$'\n'

data_path="data/naver/kin/tmp/by_user.분야별지식인"
for d in $(ls -1 ${data_path}) ; do
    echo ${d}

    python3 naver_kin_crawler.py -detail -index answer_list -match_phrase '{"user_name": "'${d}'"}'
done

