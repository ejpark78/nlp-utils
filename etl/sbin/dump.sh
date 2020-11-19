#!/usr/bin/env bash


## dump
PYTHONPATH=. utils/elasticsearch_utils.py \
    -index_list \
    -auth elastic:nlplab \
    -host https://corpus.ncsoft.com:9200 \
    > index.list

cat index.list \
    | xargs -I{} echo "\
        PYTHONPATH=. utils/elasticsearch_utils.py \
            -dump_data \
            -auth elastic:nlplab \
            -host https://corpus.ncsoft.com:9200 \
            -index {} \
    | bzip2 - > data/$(date -I)/{}.json.bz2" \
    | perl -ple 's/\s+/ /g' \
    > dump.sh

time parallel -k -j 12 --bar -a dump.sh "sh -c {}"


#        -query '{\"query\":{\"bool\":{\"must\": [{\"range\": {\"date\": {\"format\": \"yyyy-MM-dd\",\"gte\": \"2019-03-01\"}}}]}}}' \


# insert
cat index.list \
    | xargs -I{} echo "\
        bzcat data/$(date -I)/{}.json.bz2 \
            | PYTHONPATH=. venv/bin/python utils/elasticsearch_utils.py \
                -import_data\
                -index {} \
                -auth elastic:nlplab \
                -host https://corpus.ncsoft.com:9200 \
        " \
    | perl -ple 's/\s+/ /g' \
    > import-batch.sh

time parallel -k -j 8 --bar -a import-batch.sh "sh -c {}"



#index=$1
#dump_path=$PWD
#
## 파라메터 확인
#if [[ "${index}" == "" ]] ; then
#    echo "Usage: "$(basename $0)" [인덱스명: crawler-bbs-lineagem]"
#    exit 1
#fi

#bin_path=$(dirname $0)
#
#host="http://corpus.ncsoft.com:9200"
#
#mkdir -p "${dump_path}" && sync
#
#${bin_path}/../elasticsearch_utils.py \
#    -export \
#    -host "${host}" \
#    -index "${index}" \
#    | bzip2 - > "${dump_path}/${index}.$(date -I).json.bz2"
#
## 인덱스 목록 표시
## curl -s 'http://corpus.ncsoft.com:9200/_cat/indices?v&s=index&h=index,docs.count' | grep crawler-naver
