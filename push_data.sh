#!/usr/bin/env bash

# cd /usr/local/app

IFS=$'\n'

host="http://gollum06:9201"
data_path="data/dump/crawler.2018-08-18/batch"

for d in $(ls -1 ${data_path}) ; do
    echo ${d}

    bzcat ${data_path}/${d}/*.json.bz2 | python3 mongo2elastic.py -push_data -host ${host} -db_name ${d}

    mv ${data_path}/${d} ${data_path}/../${d}
done


# daum_society
# daum_sports
# jisikman_app
# nate_economy
# nate_entertainment
# nate_international
# nate_it
# nate_opinion
# nate_photo
# nate_politics
# nate_radio
# nate_society
# nate_sports
# nate_tv
# naver_economy
# naver_international
# naver_it
# naver_kin_baseball
# naver_living
# naver_opinion
# naver_politics
# naver_society
# naver_sports
# naver_tv