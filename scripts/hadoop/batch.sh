#!/usr/bin/env bash

domain="economy"
source="naver"
workdir="data/${domain}/${source}"
reducer=""

max_map=70

for year in {2002..2017} ; do
    echo "year: ${year}"

    # 형태소 분석, 개체명 인식, 키워드 추출
    input="${workdir}/${year}.json.bz2"
    output="${workdir}/${year}.pos.json.bz2"
    mapper="src/NCPreProcess.py -spark_batch -domain ${domain}"
    time ./scripts/hadoop/streaming.sh ${max_map} "${input}" "${output}" "${mapper}" "${reducer}"

    # 의존 파서
#    input="${workdir}/${year}.pos.json.bz2"
#    output="${workdir}/${year}.parsed.json.bz2"
#    mapper="java -Xms1g -Xmx1g -jar src/parser.jar dictionary/model/"
#    time ./scripts/hadoop/streaming.sh ${max_map} "${input}" "${output}" "${mapper}" "${reducer}"

    # 디비 입력
    input="${output}"
    time bzcat ${input} | mongoimport --host gollum02 --db "${source}_${domain}" --collection ${year} --upsert

    input="${output}"
    time bzcat ${input} | python3 NCElastic.py -insert_documents -es_host gollum -index "${source}_${domain}" -type ${year}

    # 문장 추출
#    input="${workdir}/${year}.json.result.bz2"
#    output="${workdir}/${year}.json.sentence.bz2"

#    mapper="src/NCPreProcess.py -extract_sentence -format text"
#    time ./scripts/hadoop/streaming.sh ${max_map} "${input}" "${output}" "${mapper}" "${reducer}"
done
