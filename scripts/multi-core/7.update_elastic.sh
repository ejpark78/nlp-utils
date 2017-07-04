#!/bin/bash

echo "running: ${0}"

# 몽고 디비 설정
db_host="172.20.78.170"
db_name="news"
collection_name_header="nate_baseball"

#es_host="gollum"
es_host="172.20.78.170"
index_name="nate_baseball"

echo "delete index: ${index_name}"
python3 NCElastic.py -delete_index -es_host "${es_host}" -index_name "${index_name}"

for year in 2016 2015 2014 2013 2012 2011 2010 2009 2008 2007 2006 2005 ; do
    date_range[${#date_range[*]}]=${year}

    echo "year: ${year}"
    time python3 NCElastic.py -make_index \
        -db_host "${db_host}" -db_name "${db_name}" -collection "${collection_name_header}_${year}" \
        -es_host "${es_host}" -index_name "${index_name}" -type_name "${year}"

#        \
#        |& tee -a "${log_dir}/${year}.log" 2>&1
done


cat 2016-04-14.json | python3 NCElastic.py -make_index


memo="

ps -ef | grep NCElastic.py | perl -ple 's/ +/\t/g;' | cut -f2 | xargs kill


python3 NCElastic.py -delete_type -index_name nate_baseball -type_name 2016

curl -k -XDELETE 'https://elastic:changeme@gollum.ncsoft.com:9200/baseball'
curl -k -XDELETE 'https://elastic:changeme@gollum.ncsoft.com:9200/baseball/2016'


curl -k -XGET 'https://elastic:changeme@gollum.ncsoft.com:9200/_mapping?pretty=true'
curl -k -XGET 'https://elastic:changeme@gollum.ncsoft.com:9200/baseball/2016/_stats?pretty=true'

curl -k -XGET 'https://elastic:changeme@gollum.ncsoft.com:9200/baseball/_settings,_mappings?pretty=true'

curl -k -XGET 'https://elastic:changeme@gollum.ncsoft.com:9200/_cat/master?v'
curl -k -XGET 'https://elastic:changeme@gollum.ncsoft.com:9200/_cat/master?help'

curl -k -XGET 'https://elastic:changeme@gollum.ncsoft.com:9200/_cat/indices?format=json&pretty'


curl -k -XGET 'https://elastic:changeme@gollum.ncsoft.com:9200/_xpack/license'


curl -k -XPUT 'https://elastic:changeme@gollum.ncsoft.com:9200/_xpack/license?acknowledge=true' -d @eunjin-park-3cf5503b-cd6d-4550-be0f-a69e560da254-v5.json


curl -k -XGET 'https://elastic:changeme@gollum.ncsoft.com:9200/baseball/_search?pretty=true' -d '{
    "sort": [{
        "date": {"order": "desc"}
    }],
    "query": {
        "bool": {
            "must": [{
                "match_phrase": {
                    "keywords.words": "한기주"
                }
            }]
        }
    }
}'


curl -k -XDELETE 'https://elastic:changeme@gollum.ncsoft.com:9200/baseball/2016/sports.news.nate.20160413n36003'


https://elastic:changeme@gollum.ncsoft.com:9200/nate_baseball/_mapping/2016?pretty=true



"
#
#curl -XDELETE 'http://gollum:9200/nate_baseball/2016/_query?pretty=true' -d ' { "query": { "match_all": {} } }'
#
#
#"filter": {range: dateRange}
#
#curl -XDELETE 'http://gollum:9200/nate_baseball/2016?timeout=5m'
#
#
#curl -XGET 'http://gollum:9200/nate_baseball/2016/_search' -d ' { "query": { "match_all": {} } }'
#
#
#                    match : {
#                        keyword: {
#                            "query": vm.keyword,
#                            "operator": "and"
#                          }
#                    }

## 검색
#time python3 NCElastic.py -es_host gollum -index_name nate_baseball -search -keyword "투수"
#
## 인덱스 생성
#time python3 NCElastic.py -delete_index -es_host "gollum" -index_name "nate_baseball"
#
## 인덱스 삭제
#curl -XDELETE 'http://gollum:9200/nate_baseball'
#
#curl -XPUT 'http://gollum:9200/nate_baseball/_search?pretty' -d '{
#    "settings" : {
#        "number_of_shards" : 10,
#        "number_of_replicas" : 1
#    }
#}'
#
## 매핑 정보 쿼리
#curl -XGET 'http://gollum:9200/nate_baseball/_mapping?pretty'
#
## 인덱스 생성
#for y in 2015 2014 2013 2012 2011 2010 2009 2008 2007 2006 2005 ; do
#    echo -e "y: ${y}"
#
#    python3 NCIndexer.py \
#        -es_host "gollum" \
#        -index_name "nate_baseball" \
#        -year "${y}" \
#        -db_name "news"
#done
#
## 인덱스 생성 테스트
#python3 NCIndexer.py \
#    -db "curl_result/prev_corpus/baseball/1.nate/2010.postagged.db" \
#    -index_name "nate_baseball" -type_name "2010" \
#    -es_host "gollum"
#
#curl 'http://gollum:9200/nate_baseball/_search?pretty' -d '
#{
#  "query" : {
#    "match" : {
#      "keyword" : "투수"
#    }
#  }
#}'
#
#curl 'gollum:9200/_search?pretty' -d '
#{
#  "query" : {
#    "match" : {
#      "keyword" : "엔씨 선발투수"
#    }
#  }
#}'


#curl 'http://gollum:9200/nate_baseball/_search?pretty' -d '
#{
#  "query" : {
#    "match_all" : {}
#  }
#}'