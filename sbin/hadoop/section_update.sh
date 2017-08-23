#!/usr/bin/env bash

domain="economy"
source="naver"
workdir="data/${domain}/${source}"
reducer=""

max_map=70

year=2016
for year in {1997..2004} ; do
    echo "year: ${year}"

    input="${workdir}/${year}.json.bz2"
    output="${workdir}/${year}.simple_id.json.bz2"
    mapper="src/UpdateSectionInfo.py"
    time ./sbin/hadoop/streaming.sh ${max_map} ${input} ${output} "${mapper}" "${reducer}"
done

#real	129m40.321s
#user	0m54.436s
#sys	0m8.620s
#
#input="${workdir}/${year}.json.bz2"
#output="${workdir}/${year}.ner.json.bz2"
#mapper="src/NCPreProcess.py -spark_batch -domain ${domain}"
#time ./scripts/hadoop/streaming.sh ${max_map} ${input} ${output} "${mapper}" "${reducer}"

#real	28m23.329s
#user	0m46.964s
#sys	0m6.184s
#
#
#input="${workdir}/${year}.ner.json.bz2"
#output="${workdir}/${year}.simple.json.bz2"
#mapper="src/filter.py"
#time ./scripts/hadoop/streaming.sh ${max_map} ${input} ${output} "${mapper}" "${reducer}"
#
