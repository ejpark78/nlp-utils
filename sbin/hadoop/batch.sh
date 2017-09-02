#!/usr/bin/env bash

domain="baseball"
source="nate"
workdir="data/${domain}/${source}"
reducer=""

max_map=75

corpus_path="/corpus/news/${domain}/${source}"

#for year in {2004..2017} ; do
for year in {2005..2017} ; do
    echo "year: ${year}"

    # 형태소 분석, 개체명 인식, 키워드 추출
    input="${corpus_path}/${year}.json.bz2"
    output="${year}.pos.json.bz2"
    mapper="src/NCPreProcess.py -spark_batch -domain ${domain}"
#    time ./sbin/hadoop/streaming.sh ${max_map} "${input}" "${output}" "${mapper}" "${reducer}"

    # 의존 파서
    input="${corpus_path}/${year}.pos.json.bz2"
    output="${year}.parsed.json.bz2"
    mapper="java -Xms1g -Xmx1g -jar src/parser.jar dictionary/model/"
#    time ./sbin/hadoop/streaming.sh ${max_map} "${input}" "${output}" "${mapper}" "${reducer}"

    # 디비 입력
#    input="${output}"
#    time bzcat ${input} | mongoimport --host gollum02 --db "${source}_${domain}" --collection ${year} --upsert

#    input="${output}"
    input="${workdir}/${year}.parsed.json.bz2"
    time bzcat ${input} | python3 NCElastic.py -insert_documents -es_host gollum -index "${source}_${domain}" -type ${year}

    # 문장 추출
#    input="${workdir}/${year}.json.result.bz2"
#    output="${workdir}/${year}.json.sentence.bz2"

#    mapper="src/NCPreProcess.py -extract_sentence -format text"
#    time ./sbin/hadoop/streaming.sh ${max_map} "${input}" "${output}" "${mapper}" "${reducer}"
done
